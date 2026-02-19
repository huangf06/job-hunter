"""
Google Calendar REST Client
============================

Project-agnostic Google Calendar client using REST API + OAuth2 tokens.
Shares token file with google-calendar-mcp (atomic read-modify-write).

Dependencies: requests (+ stdlib: json, time, dataclasses, datetime, pathlib, tempfile)
"""

import json
import time
import tempfile
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional, Tuple

import requests

# Google Calendar API base
API_BASE = "https://www.googleapis.com/calendar/v3"

# Default paths (shared with google-calendar-mcp)
DEFAULT_TOKENS_PATH = Path.home() / ".config" / "google-calendar-mcp" / "tokens.json"
DEFAULT_CREDENTIALS_PATH = Path.home() / ".config" / "gcp-oauth.keys.json"


@dataclass
class CalendarEvent:
    id: str
    summary: str
    start: datetime  # timezone-aware
    end: datetime
    location: Optional[str] = None
    description: Optional[str] = None
    attendees: List[str] = field(default_factory=list)
    meet_link: Optional[str] = None


class GoogleCalendarClient:
    """REST client for Google Calendar API with automatic token refresh."""

    def __init__(
        self,
        tokens_path: Path = None,
        credentials_path: Path = None,
        token_key: str = "normal",
    ):
        self.tokens_path = Path(tokens_path or DEFAULT_TOKENS_PATH)
        self.credentials_path = Path(credentials_path or DEFAULT_CREDENTIALS_PATH)
        self.token_key = token_key

        # Load credentials (client_id, client_secret, token_uri)
        creds = json.loads(self.credentials_path.read_text(encoding="utf-8"))
        installed = creds.get("installed", creds.get("web", {}))
        self.client_id = installed["client_id"]
        self.client_secret = installed["client_secret"]
        self.token_uri = installed.get("token_uri", "https://oauth2.googleapis.com/token")

        # Load tokens
        self._tokens = self._load_tokens()

    # ========== Token Management ==========

    def _load_tokens(self) -> dict:
        """Load token entry for our key."""
        all_tokens = json.loads(self.tokens_path.read_text(encoding="utf-8"))
        entry = all_tokens.get(self.token_key)
        if not entry:
            raise ValueError(f"Token key '{self.token_key}' not found in {self.tokens_path}")
        return entry

    def _save_tokens(self) -> None:
        """Atomic read-modify-write: update only our key, preserve others."""
        all_tokens = json.loads(self.tokens_path.read_text(encoding="utf-8"))
        all_tokens[self.token_key] = self._tokens

        # Write via temp file + rename for atomicity (safe with MCP)
        parent = self.tokens_path.parent
        parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=str(parent), suffix=".tmp")
        try:
            with open(fd, "w", encoding="utf-8") as f:
                json.dump(all_tokens, f, indent=2)
            # On Windows, shutil.move handles cross-device and overwrites
            shutil.move(tmp_path, str(self.tokens_path))
        except Exception:
            Path(tmp_path).unlink(missing_ok=True)
            raise

    def _ensure_valid_token(self) -> str:
        """Return a valid access token, refreshing if expired."""
        expiry_ms = self._tokens.get("expiry_date", 0)
        now_ms = int(time.time() * 1000)

        # Refresh if token expires within 60 seconds
        if now_ms >= expiry_ms - 60_000:
            self._refresh_token()

        return self._tokens["access_token"]

    def _refresh_token(self) -> None:
        """Refresh the access token via Google's token endpoint."""
        refresh_token = self._tokens.get("refresh_token")
        if not refresh_token:
            raise RuntimeError("No refresh_token available — re-authenticate via MCP")

        resp = requests.post(
            self.token_uri,
            data={
                "grant_type": "refresh_token",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": refresh_token,
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        self._tokens["access_token"] = data["access_token"]
        self._tokens["expiry_date"] = int(time.time() * 1000) + data["expires_in"] * 1000
        if "refresh_token" in data:
            self._tokens["refresh_token"] = data["refresh_token"]

        self._save_tokens()

    # ========== HTTP Helper ==========

    def _request(self, method: str, path: str, **kwargs) -> dict:
        """Authenticated HTTP request to Calendar API."""
        token = self._ensure_valid_token()
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {token}"

        url = f"{API_BASE}{path}" if path.startswith("/") else path
        resp = requests.request(method, url, headers=headers, timeout=30, **kwargs)
        resp.raise_for_status()

        if resp.status_code == 204 or not resp.content:
            return {}
        return resp.json()

    # ========== Event Parsing ==========

    @staticmethod
    def _parse_event(item: dict) -> CalendarEvent:
        """Parse a Calendar API event item into CalendarEvent."""
        start_raw = item.get("start", {})
        end_raw = item.get("end", {})

        start = GoogleCalendarClient._parse_datetime(start_raw)
        end = GoogleCalendarClient._parse_datetime(end_raw)

        # Extract Google Meet link
        meet_link = None
        if item.get("hangoutLink"):
            meet_link = item["hangoutLink"]
        for ep in item.get("conferenceData", {}).get("entryPoints", []):
            if ep.get("entryPointType") == "video":
                meet_link = ep.get("uri")
                break

        attendees = [
            a["email"]
            for a in item.get("attendees", [])
            if "email" in a
        ]

        return CalendarEvent(
            id=item["id"],
            summary=item.get("summary", "(No title)"),
            start=start,
            end=end,
            location=item.get("location"),
            description=item.get("description"),
            attendees=attendees,
            meet_link=meet_link,
        )

    @staticmethod
    def _parse_datetime(dt_dict: dict) -> datetime:
        """Parse dateTime or date from Calendar API response."""
        if "dateTime" in dt_dict:
            return datetime.fromisoformat(dt_dict["dateTime"])
        elif "date" in dt_dict:
            # All-day event: treat as midnight in UTC
            return datetime.strptime(dt_dict["date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        raise ValueError(f"Cannot parse datetime: {dt_dict}")

    # ========== Public API ==========

    def list_events(
        self,
        time_min: datetime,
        time_max: datetime,
        calendar_id: str = "primary",
        max_results: int = 250,
    ) -> List[CalendarEvent]:
        """List events in a time range."""
        events = []
        page_token = None

        while True:
            params = {
                "timeMin": time_min.isoformat(),
                "timeMax": time_max.isoformat(),
                "singleEvents": "true",
                "orderBy": "startTime",
                "maxResults": min(max_results - len(events), 250),
            }
            if page_token:
                params["pageToken"] = page_token

            data = self._request("GET", f"/calendars/{calendar_id}/events", params=params)

            for item in data.get("items", []):
                if item.get("status") == "cancelled":
                    continue
                events.append(self._parse_event(item))

            page_token = data.get("nextPageToken")
            if not page_token or len(events) >= max_results:
                break

        return events

    def get_free_busy(
        self,
        time_min: datetime,
        time_max: datetime,
        calendar_ids: List[str] = None,
    ) -> List[Tuple[datetime, datetime]]:
        """Get merged busy intervals via FreeBusy API."""
        if calendar_ids is None:
            calendar_ids = ["primary"]

        body = {
            "timeMin": time_min.isoformat(),
            "timeMax": time_max.isoformat(),
            "items": [{"id": cid} for cid in calendar_ids],
        }

        data = self._request("POST", "/freeBusy", json=body)

        # Collect all busy intervals across calendars
        intervals = []
        for cal_data in data.get("calendars", {}).values():
            for busy in cal_data.get("busy", []):
                start = datetime.fromisoformat(busy["start"])
                end = datetime.fromisoformat(busy["end"])
                intervals.append((start, end))

        # Sort and merge overlapping intervals
        return self._merge_intervals(intervals)

    @staticmethod
    def _merge_intervals(intervals: List[Tuple[datetime, datetime]]) -> List[Tuple[datetime, datetime]]:
        """Merge overlapping time intervals."""
        if not intervals:
            return []

        sorted_intervals = sorted(intervals, key=lambda x: x[0])
        merged = [sorted_intervals[0]]

        for start, end in sorted_intervals[1:]:
            prev_start, prev_end = merged[-1]
            if start <= prev_end:
                merged[-1] = (prev_start, max(prev_end, end))
            else:
                merged.append((start, end))

        return merged

    def create_event(
        self,
        summary: str,
        start: datetime,
        end: datetime,
        calendar_id: str = "primary",
        description: str = None,
        location: str = None,
        attendees: List[str] = None,
        add_meet: bool = False,
    ) -> str:
        """Create a calendar event. Returns event ID."""
        body = {
            "summary": summary,
            "start": {"dateTime": start.isoformat()},
            "end": {"dateTime": end.isoformat()},
        }
        if description:
            body["description"] = description
        if location:
            body["location"] = location
        if attendees:
            body["attendees"] = [{"email": e} for e in attendees]
        if add_meet:
            body["conferenceData"] = {
                "createRequest": {"requestId": f"meet-{int(time.time())}"}
            }

        params = {}
        if add_meet:
            params["conferenceDataVersion"] = "1"

        data = self._request(
            "POST",
            f"/calendars/{calendar_id}/events",
            json=body,
            params=params,
        )
        return data["id"]

    def find_available_slots(
        self,
        time_min: datetime,
        time_max: datetime,
        duration_minutes: int,
        buffer_minutes: int = 60,
        calendar_ids: List[str] = None,
    ) -> List[Tuple[datetime, datetime]]:
        """Find free windows of at least `duration_minutes` between busy blocks.

        Args:
            buffer_minutes: padding before and after each busy block.

        Returns list of (start, end) tuples for available windows.
        """
        busy = self.get_free_busy(time_min, time_max, calendar_ids)

        # Expand busy intervals with buffer
        buffered = []
        buf = timedelta(minutes=buffer_minutes)
        for b_start, b_end in busy:
            buffered.append((b_start - buf, b_end + buf))

        # Re-merge after buffering
        buffered = self._merge_intervals(buffered)

        # Find gaps
        duration = timedelta(minutes=duration_minutes)
        free_slots = []
        cursor = time_min

        for b_start, b_end in buffered:
            if cursor + duration <= b_start:
                free_slots.append((cursor, b_start))
            cursor = max(cursor, b_end)

        # Remaining time after last busy block
        if cursor + duration <= time_max:
            free_slots.append((cursor, time_max))

        return free_slots
