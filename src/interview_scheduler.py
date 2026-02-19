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

    def _score_slot(self, start: datetime, end: datetime, ai_score: Optional[float]) -> tuple:
        """Score a candidate slot. Returns (score, reason_parts)."""
        score = 5.0
        reasons = []

        hour = start.hour
        weekday = start.weekday()  # 0=Mon ... 4=Fri

        # Time-of-day scoring
        if self.peak_start.hour <= hour < self.peak_end.hour:
            score += 3.0
            reasons.append("peak hours (10-12)")
        elif 9 <= hour < 10:
            score += 1.0
            reasons.append("early morning")
        elif 13 <= hour < 15:
            score += 1.5
            reasons.append("early afternoon")
        elif 15 <= hour < 17:
            score += 0.5
            reasons.append("late afternoon")

        # Day-of-week scoring
        if weekday <= 2:  # Mon-Wed
            score += 1.0
            reasons.append("Mon-Wed")
        elif weekday == 3:  # Thu
            score += 0.5
            reasons.append("Thu")
        # Fri: +0

        # High-priority company bonus
        if ai_score is not None and ai_score >= 7.0:
            if self.peak_start.hour <= hour < self.peak_end.hour:
                score += 1.0
                reasons.append("priority company + peak")

        score = min(10.0, score)
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
