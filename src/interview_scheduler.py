"""
Interview Scheduler
====================

Smart interview scheduling that combines Google Calendar availability
with job database context (AI scores, company priority).

Usage:
    from src.interview_scheduler import InterviewScheduler
    scheduler = InterviewScheduler()
    slots = scheduler.suggest_slots("FareHarbor", duration_minutes=30, days=14)
"""

import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, time as dt_time, timezone
from pathlib import Path
from typing import List, Optional, Dict
from zoneinfo import ZoneInfo

import yaml

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.google_calendar import GoogleCalendarClient
from src.db.job_db import JobDatabase


@dataclass
class SuggestedSlot:
    start: datetime
    end: datetime
    score: float   # 0-10
    reason: str    # human-readable


class InterviewScheduler:
    """Smart interview scheduler: calendar availability + job priority."""

    def __init__(self):
        config_path = PROJECT_ROOT / "config" / "ai_config.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            full_config = yaml.safe_load(f)

        self.config = full_config.get("interview_scheduler", {})
        self.tz = ZoneInfo(self.config.get("timezone", "Europe/Amsterdam"))

        # Parse working hours
        wh = self.config.get("working_hours", {})
        self.work_start = self._parse_time(wh.get("start", "09:00"))
        self.work_end = self._parse_time(wh.get("end", "17:00"))

        # Parse peak hours
        ph = self.config.get("peak_hours", {})
        self.peak_start = self._parse_time(ph.get("start", "10:00"))
        self.peak_end = self._parse_time(ph.get("end", "12:00"))

        self.buffer_minutes = self.config.get("buffer_minutes", 60)

        # Personal energy profile (candidate-specific calibration)
        energy = self.config.get("candidate_energy", {})
        self.energy_morning_peak = energy.get("morning_peak", 2.0)
        self.energy_morning_warmup = energy.get("morning_warmup", 1.0)
        self.energy_afternoon_focus = energy.get("afternoon_focus", -0.5)
        self.energy_post_lunch_dip = energy.get("post_lunch_dip", -1.5)
        self.energy_late_afternoon = energy.get("late_afternoon", -1.0)

        self.calendar = GoogleCalendarClient()
        self.db = JobDatabase()

    @staticmethod
    def _parse_time(s: str) -> dt_time:
        parts = s.split(":")
        return dt_time(int(parts[0]), int(parts[1]))

    # ========== DB Lookup ==========

    def _lookup_company_score(self, company: str) -> Optional[float]:
        """Get max AI score for a company from the database."""
        rows = self.db.execute(
            """
            SELECT MAX(a.ai_score) as max_score
            FROM jobs j
            JOIN job_analysis a ON j.id = a.job_id
            WHERE LOWER(j.company) LIKE ?
            """,
            (f"%{company.lower()}%",),
        )
        if rows and rows[0].get("max_score") is not None:
            return float(rows[0]["max_score"])
        return None

    # ========== Slot Scoring ==========
    #
    # Scoring philosophy (career coaching best practices):
    #
    # A good interview slot optimizes THREE perspectives:
    #
    # 1. CANDIDATE performance — your cognitive peak, preparation buffer
    #    - 10:00-11:30 is peak cognitive window for most people
    #    - Post-lunch (13:00-13:30) dip; 14:00-15:30 recovery
    #    - Avoid first-thing (09:00) if you need warmup time
    #
    # 2. INTERVIEWER receptiveness — their energy and attention
    #    - Monday morning: catching up on emails, standups, not focused on you
    #    - Monday afternoon: settled in, acceptable
    #    - Tuesday-Wednesday: peak week engagement, best days
    #    - Thursday: still good, slight wind-down
    #    - Friday morning: acceptable; Friday afternoon: mentally checked out
    #    - Mid-morning (10-12): interviewer is warmed up but not yet fatigued
    #    - Late afternoon (16:00+): they want to go home
    #
    # 3. STRATEGIC factors — impression and context
    #    - Tue/Wed 10:00-11:30 is the "golden window" (both sides peak)
    #    - Being early in the interview day avoids decision fatigue
    #    - Back-to-back interviews same day drain preparation quality
    #    - High-priority companies deserve golden-window slots

    def _score_slot(self, start: datetime, end: datetime, ai_score: Optional[float]) -> tuple:
        """Score a candidate slot on three dimensions. Returns (score, reason_parts).

        Dimensions:
        - Candidate cognitive performance (time of day)
        - Interviewer receptiveness (day of week + time)
        - Strategic fit (golden window, priority company)
        """
        score = 3.0  # base
        reasons = []

        hour = start.hour
        minute = start.minute
        h_frac = hour + minute / 60.0  # e.g. 10:30 = 10.5
        weekday = start.weekday()  # 0=Mon ... 4=Fri

        # --- Dimension 1: Candidate cognitive performance (configurable) ---
        if 10.0 <= h_frac < 11.5:
            score += 3.0 + self.energy_morning_peak
            reasons.append("candidate peak (10-11:30)")
        elif 9.0 <= h_frac < 10.0:
            score += 1.5 + self.energy_morning_warmup
            reasons.append("candidate warmup (9-10)")
        elif 14.0 <= h_frac < 15.5:
            score += 2.0 + self.energy_afternoon_focus
            reasons.append("afternoon (not your best)")
        elif 13.0 <= h_frac < 14.0:
            score += 0.5 + self.energy_post_lunch_dip
            reasons.append("post-lunch dip")
        elif 15.5 <= h_frac < 17.0:
            score += 1.0 + self.energy_late_afternoon
            reasons.append("late afternoon")

        # --- Dimension 2: Interviewer receptiveness (max +3.0) ---
        if weekday in (1, 2):  # Tue, Wed
            if 10.0 <= h_frac < 12.0:
                score += 3.0
                reasons.append("interviewer peak (Tue/Wed morning)")
            elif 14.0 <= h_frac < 16.0:
                score += 2.0
                reasons.append("interviewer engaged (Tue/Wed afternoon)")
            else:
                score += 1.5
                reasons.append("Tue/Wed")
        elif weekday == 3:  # Thu
            if 10.0 <= h_frac < 12.0:
                score += 2.5
                reasons.append("interviewer good (Thu morning)")
            else:
                score += 1.0
                reasons.append("Thu")
        elif weekday == 0:  # Mon
            if h_frac < 12.0:
                score -= 0.5
                reasons.append("Mon morning (interviewer settling in)")
            else:
                score += 1.0
                reasons.append("Mon afternoon (settled)")
        elif weekday == 4:  # Fri
            if h_frac < 12.0:
                score += 0.5
                reasons.append("Fri morning (acceptable)")
            else:
                score -= 1.0
                reasons.append("Fri afternoon (interviewer checked out)")

        # --- Dimension 3: Strategic bonus (max +2.0) ---
        # Golden window: Tue/Wed 10:00-11:30
        is_golden = weekday in (1, 2) and 10.0 <= h_frac < 11.5
        if is_golden:
            score += 1.0
            reasons.append("GOLDEN WINDOW")

        # High-priority company deserves best slots
        if ai_score is not None and ai_score >= 7.0 and is_golden:
            score += 1.0
            reasons.append("priority company")

        score = max(0.0, min(10.0, score))
        return score, reasons

    # ========== Slot Generation ==========

    def _generate_candidate_slots(
        self,
        free_windows: list,
        duration_minutes: int,
        step_minutes: int = 30,
    ) -> List[tuple]:
        """Generate candidate (start, end) from free windows, filtered to working hours on weekdays."""
        duration = timedelta(minutes=duration_minutes)
        step = timedelta(minutes=step_minutes)
        candidates = []

        for win_start, win_end in free_windows:
            # Localize to configured timezone
            ws = win_start.astimezone(self.tz)
            we = win_end.astimezone(self.tz)

            # Snap to next step boundary
            cursor = ws
            if cursor.minute % step_minutes != 0:
                cursor = cursor.replace(
                    minute=(cursor.minute // step_minutes + 1) * step_minutes % 60,
                    second=0, microsecond=0,
                )
                if (cursor.minute // step_minutes + 1) * step_minutes >= 60:
                    cursor = cursor.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)

            while cursor + duration <= we:
                # Weekday only (Mon=0 .. Fri=4)
                if cursor.weekday() < 5:
                    slot_start_time = cursor.time()
                    slot_end_time = (cursor + duration).time()

                    # Within working hours (both start and end must fall within the same working day)
                    if (slot_start_time >= self.work_start
                            and slot_end_time <= self.work_end
                            and slot_end_time > slot_start_time):  # reject midnight wrap
                        candidates.append((cursor, cursor + duration))

                cursor += step

        return candidates

    # ========== Public API ==========

    def suggest_slots(
        self,
        company: str,
        duration_minutes: int = 60,
        days: int = 14,
        num_slots: int = 5,
    ) -> List[SuggestedSlot]:
        """Suggest top N interview slots ranked by scoring algorithm.

        Args:
            company: Company name (used for DB priority lookup).
            duration_minutes: Interview length.
            days: How many days ahead to search.
            num_slots: How many slots to return.

        Returns:
            List of SuggestedSlot, sorted by score descending.
        """
        ai_score = self._lookup_company_score(company)
        if ai_score is not None:
            print(f"[Scheduler] {company} — AI score: {ai_score:.1f}")
        else:
            print(f"[Scheduler] {company} — no AI score found")

        now = datetime.now(self.tz)
        time_min = now
        time_max = now + timedelta(days=days)

        # Get free windows from calendar
        free_windows = self.calendar.find_available_slots(
            time_min=time_min,
            time_max=time_max,
            duration_minutes=duration_minutes,
            buffer_minutes=self.buffer_minutes,
        )

        if not free_windows:
            print("[Scheduler] No free windows found")
            return []

        # Generate and score candidates
        candidates = self._generate_candidate_slots(free_windows, duration_minutes)

        scored = []
        for start, end in candidates:
            slot_score, reasons = self._score_slot(start, end, ai_score)
            scored.append(SuggestedSlot(
                start=start,
                end=end,
                score=round(slot_score, 1),
                reason=", ".join(reasons) if reasons else "standard slot",
            ))

        # Sort by score descending
        scored.sort(key=lambda s: s.score, reverse=True)

        # Greedy de-conflict: no overlapping picks
        selected = []
        for slot in scored:
            if len(selected) >= num_slots:
                break
            # Check for overlap with already-selected slots
            overlaps = False
            for picked in selected:
                if slot.start < picked.end and slot.end > picked.start:
                    overlaps = True
                    break
            if not overlaps:
                selected.append(slot)

        return selected

    def suggest_availability(
        self,
        company: str,
        duration_minutes: int = 30,
        days: int = 14,
    ) -> Dict[str, List[SuggestedSlot]]:
        """Return ALL valid slots grouped by date (for 'pick your times' scenarios).

        Returns:
            Dict mapping date strings (e.g. "Mon Feb 24") to lists of SuggestedSlot.
        """
        ai_score = self._lookup_company_score(company)
        if ai_score is not None:
            print(f"[Scheduler] {company} — AI score: {ai_score:.1f}")
        else:
            print(f"[Scheduler] {company} — no AI score found")

        now = datetime.now(self.tz)
        time_min = now
        time_max = now + timedelta(days=days)

        free_windows = self.calendar.find_available_slots(
            time_min=time_min,
            time_max=time_max,
            duration_minutes=duration_minutes,
            buffer_minutes=self.buffer_minutes,
        )

        if not free_windows:
            print("[Scheduler] No free windows found")
            return {}

        candidates = self._generate_candidate_slots(free_windows, duration_minutes)

        # Score and group by date
        by_date: Dict[str, List[SuggestedSlot]] = {}
        for start, end in candidates:
            slot_score, reasons = self._score_slot(start, end, ai_score)
            slot = SuggestedSlot(
                start=start,
                end=end,
                score=round(slot_score, 1),
                reason=", ".join(reasons) if reasons else "standard slot",
            )
            date_key = start.strftime("%a %b %d")
            by_date.setdefault(date_key, []).append(slot)

        return by_date


# ========== CLI Formatting Helpers ==========

def format_slots(slots: List[SuggestedSlot]) -> str:
    """Format suggested slots for terminal output."""
    if not slots:
        return "No available slots found."

    lines = []
    lines.append(f"\n{'='*60}")
    lines.append(f"  TOP {len(slots)} INTERVIEW SLOTS")
    lines.append(f"{'='*60}")

    for i, slot in enumerate(slots, 1):
        date_str = slot.start.strftime("%a %b %d")
        time_str = f"{slot.start.strftime('%H:%M')}-{slot.end.strftime('%H:%M')}"
        score_color = "\033[92m" if slot.score >= 8 else "\033[93m" if slot.score >= 6 else "\033[0m"
        reset = "\033[0m"

        lines.append(f"  {i}. {score_color}[{slot.score:.1f}]{reset}  {date_str}  {time_str}")
        lines.append(f"     {slot.reason}")

    lines.append(f"{'='*60}")
    return "\n".join(lines)


def format_availability(by_date: Dict[str, List[SuggestedSlot]]) -> str:
    """Format all available slots grouped by date."""
    if not by_date:
        return "No available slots found."

    lines = []
    lines.append(f"\n{'='*60}")
    lines.append(f"  AVAILABLE SLOTS")
    lines.append(f"{'='*60}")

    total = 0
    for date_key, slots in by_date.items():
        lines.append(f"\n  {date_key}:")
        for slot in slots:
            time_str = f"{slot.start.strftime('%H:%M')}-{slot.end.strftime('%H:%M')}"
            lines.append(f"    [{slot.score:.1f}] {time_str}  ({slot.reason})")
            total += 1

    lines.append(f"\n  Total: {total} slots across {len(by_date)} days")
    lines.append(f"{'='*60}")
    return "\n".join(lines)
