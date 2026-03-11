"""
Gmail IMAP Client for Job Hunter
================================

Simplified Gmail IMAP client for reading job-related emails.
Based on mail_processor implementation.

Requires: GMAIL_EMAIL and GMAIL_APP_PASSWORD environment variables.
See docs/gmail_setup.md for setup instructions.

Usage:
    from src.gmail_client import GmailClient
    
    with GmailClient() as client:
        emails = client.search_emails(
            subject_keywords=["interview", "FareHarbor"],
            lookback_days=7
        )
"""

import os
import re
import email
import logging
from email import message as email_message
from email.header import decode_header
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from pathlib import Path

# Auto-load .env so credentials work without manual export
PROJECT_ROOT = Path(__file__).parent.parent
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env", override=True)
except ImportError:
    pass  # dotenv not installed, rely on env vars directly

logger = logging.getLogger(__name__)

# Optional import - gracefully handle if not installed
try:
    import imapclient
    IMAPCLIENT_AVAILABLE = True
except ImportError:
    IMAPCLIENT_AVAILABLE = False


class GmailClient:
    """Simplified Gmail IMAP client for job hunting workflow."""

    IMAP_SERVER = "imap.gmail.com"
    IMAP_PORT = 993

    def __init__(self, email_addr: str = None, app_password: str = None):
        if not IMAPCLIENT_AVAILABLE:
            raise ImportError(
                "imapclient is required. Install with: pip install imapclient>=3.0.0"
            )

        self.email_addr = email_addr or os.getenv('GMAIL_EMAIL')
        # Clean up password: replace various whitespace chars with regular space, strip
        raw_password = app_password or os.getenv('GMAIL_APP_PASSWORD', '')
        # Replace non-breaking spaces and other unicode whitespace with regular space
        self.app_password = ' '.join(raw_password.split())
        self.client = None

        if not self.email_addr or not self.app_password:
            raise ValueError(
                "GMAIL_EMAIL and GMAIL_APP_PASSWORD must be set. "
                "See docs/gmail_setup.md for instructions."
            )

    def connect(self) -> bool:
        """Connect and authenticate to Gmail IMAP."""
        try:
            logger.info(f"Connecting to Gmail IMAP as {self.email_addr}...")
            self.client = imapclient.IMAPClient(
                self.IMAP_SERVER, 
                port=self.IMAP_PORT, 
                ssl=True, 
                timeout=60
            )
            self.client.login(self.email_addr, self.app_password)
            logger.info("Connected to Gmail IMAP")
            return True
        except Exception as e:
            logger.error(f"IMAP connection failed: {e}")
            self.client = None
            raise ConnectionError(f"Failed to connect to Gmail IMAP: {e}")

    def disconnect(self):
        """Disconnect from IMAP server."""
        if self.client:
            try:
                self.client.logout()
                logger.info("Disconnected from Gmail IMAP")
            except Exception as e:
                logger.debug(f"Error during disconnect: {e}")
            finally:
                self.client = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return False

    def _decode_header_value(self, value: str) -> str:
        """Decode RFC2047-encoded header values."""
        if not value:
            return ""
        decoded_parts = decode_header(value)
        result = []
        for part, charset in decoded_parts:
            if isinstance(part, bytes):
                try:
                    result.append(part.decode(charset or 'utf-8', errors='ignore'))
                except Exception:
                    result.append(part.decode('utf-8', errors='ignore'))
            else:
                result.append(part)
        return ''.join(result)

    def _extract_body(self, msg: email_message.Message) -> str:
        """Extract email body text, preferring plain text over HTML."""
        body = ""

        if msg.is_multipart():
            # First try to find plain text
            for part in msg.walk():
                content_type = part.get_content_type()
                disposition = str(part.get("Content-Disposition", ""))
                if "attachment" in disposition:
                    continue
                if content_type == "text/plain":
                    try:
                        charset = part.get_content_charset() or 'utf-8'
                        body = part.get_payload(decode=True).decode(charset, errors='ignore')
                        break
                    except Exception:
                        continue

            # Fallback to HTML if no plain text
            if not body:
                for part in msg.walk():
                    content_type = part.get_content_type()
                    disposition = str(part.get("Content-Disposition", ""))
                    if "attachment" in disposition:
                        continue
                    if content_type == "text/html":
                        try:
                            charset = part.get_content_charset() or 'utf-8'
                            html = part.get_payload(decode=True).decode(charset, errors='ignore')
                            # Simple HTML to text conversion
                            body = re.sub(r'<[^>]+>', ' ', html)
                            body = re.sub(r'\s+', ' ', body).strip()
                            break
                        except Exception:
                            continue
        else:
            try:
                charset = msg.get_content_charset() or 'utf-8'
                body = msg.get_payload(decode=True).decode(charset, errors='ignore')
            except Exception:
                pass

        return body[:10000]  # Limit to 10KB

    def search_emails(
        self,
        subject_keywords: List[str] = None,
        lookback_days: int = 30,
        max_results: int = 50,
        unread_only: bool = False,
        folder: str = '[Gmail]/All Mail'
    ) -> List[Dict[str, Any]]:
        """
        Search emails using UIDs.

        Args:
            subject_keywords: Filter by subject keywords (case-insensitive).
                Uses server-side IMAP SUBJECT search for efficiency.
            lookback_days: How many days back to search
            max_results: Maximum emails to return
            unread_only: If True, only search unread emails
            folder: IMAP folder to search. Defaults to '[Gmail]/All Mail'
                which includes archived emails. Use 'INBOX' for inbox only.

        Returns:
            List of email dicts with: uid, message_id, subject, sender, date, body
        """
        if not self.client:
            raise ConnectionError("Not connected to IMAP server")

        self.client.select_folder(folder)

        since_date = datetime.now() - timedelta(days=lookback_days)

        # Build server-side search criteria for each keyword (OR logic)
        # and intersect with date + read status
        all_uids = set()
        base_criteria = ['SINCE', since_date]
        if unread_only:
            base_criteria.insert(0, 'UNSEEN')

        if subject_keywords:
            for kw in subject_keywords:
                criteria = base_criteria + ['SUBJECT', kw]
                uids = self.client.search(criteria)
                all_uids.update(uids)
        else:
            all_uids = set(self.client.search(base_criteria))

        uids = sorted(all_uids)
        logger.info(f"Found {len(uids)} emails since {since_date.strftime('%d-%b-%Y')} in {folder}")

        if not uids:
            return []

        # Fetch newest first, limit count
        uids_to_fetch = sorted(uids, reverse=True)[:max_results]

        # Fetch all at once; use BODY.PEEK[] to avoid marking as read
        messages = self.client.fetch(uids_to_fetch, ['BODY.PEEK[]', 'RFC822.SIZE'])

        emails = []
        for uid in uids_to_fetch:
            try:
                raw = messages.get(uid)
                if not raw:
                    continue

                raw_bytes = raw.get(b'BODY[]') or raw.get(b'RFC822')
                if not raw_bytes:
                    continue

                msg = email.message_from_bytes(raw_bytes)

                subject = self._decode_header_value(msg.get("Subject", ""))
                sender = self._decode_header_value(msg.get("From", ""))
                date_str = msg.get("Date", "")
                rfc822_message_id = msg.get("Message-ID", "")

                body = self._extract_body(msg)

                emails.append({
                    'uid': uid,
                    'message_id': rfc822_message_id,
                    'subject': subject,
                    'sender': sender,
                    'date': date_str,
                    'body': body,
                    'snippet': body[:300] + "..." if len(body) > 300 else body
                })
                logger.debug(f"Found email: {subject[:60]}")

            except Exception as e:
                logger.error(f"Error processing UID {uid}: {e}")
                continue

        logger.info(f"Returning {len(emails)} matching emails")
        return emails

    def get_email_by_subject(
        self,
        subject_pattern: str,
        lookback_days: int = 14
    ) -> Optional[Dict[str, Any]]:
        """
        Find a single email by subject pattern (partial match).

        Args:
            subject_pattern: Subject pattern to search for
            lookback_days: How many days back to search

        Returns:
            Email dict or None if not found
        """
        emails = self.search_emails(
            subject_keywords=[subject_pattern],
            lookback_days=lookback_days,
            max_results=10
        )
        return emails[0] if emails else None

    def test_connection(self) -> str:
        """Test connection and return email address."""
        if not self.client:
            self.connect()
        info = self.client.select_folder('INBOX')
        count = info.get(b'EXISTS', 0)
        logger.info(f"Inbox has {count} messages")
        return self.email_addr


def format_email_for_display(email_data: Dict[str, Any]) -> str:
    """Format an email for terminal display."""
    lines = []
    lines.append("=" * 70)
    lines.append(f"Subject: {email_data.get('subject', 'N/A')}")
    lines.append(f"From: {email_data.get('sender', 'N/A')}")
    lines.append(f"Date: {email_data.get('date', 'N/A')}")
    lines.append("-" * 70)
    
    body = email_data.get('body', '')
    # Wrap long lines
    wrapped_body = []
    for line in body.split('\n'):
        if len(line) > 80:
            # Simple word wrap
            words = line.split(' ')
            current_line = ""
            for word in words:
                if len(current_line) + len(word) + 1 <= 80:
                    current_line += word + " "
                else:
                    wrapped_body.append(current_line.rstrip())
                    current_line = word + " "
            if current_line:
                wrapped_body.append(current_line.rstrip())
        else:
            wrapped_body.append(line)
    
    lines.extend(wrapped_body)
    lines.append("=" * 70)
    return "\n".join(lines)
