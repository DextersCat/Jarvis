"""
Calendar Service - Google Calendar Integration
Handles OAuth 2.0 authentication and event retrieval for JARVIS
"""
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from tzlocal import get_localzone
import pytz

# Allow insecure transport for localhost OAuth (development only)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
import pytz

# Import config
from core.config import (
    SCOPES_CALENDAR,
    CALENDAR_TOKEN_FILE,
    CREDENTIALS_FILE,
    TIMEZONE_DEFAULT
)

logger = logging.getLogger(__name__)


class CalendarService:
    """Google Calendar integration for JARVIS"""
    
    def __init__(self, credentials_path: Optional[Path] = None):
        """
        Initialize Calendar Service
        
        Args:
            credentials_path: Path to OAuth credentials.json
                            (defaults to config.CREDENTIALS_FILE)
        """
        self.credentials_path = credentials_path or CREDENTIALS_FILE
        self.token_file = CALENDAR_TOKEN_FILE
        self.scopes = SCOPES_CALENDAR
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Handle OAuth 2.0 authentication with Google Calendar"""
        creds = None
        
        # Load existing token
        if self.token_file.exists():
            try:
                creds = Credentials.from_authorized_user_file(
                    str(self.token_file), 
                    self.scopes
                )
                logger.info("Loaded existing calendar credentials")
            except Exception as e:
                logger.warning(f"Failed to load calendar token: {e}")
        
        # Refresh or obtain new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    logger.info("Refreshed calendar credentials")
                except Exception as e:
                    logger.error(f"Failed to refresh token: {e}")
                    creds = None
            
            if not creds:
                if not self.credentials_path.exists():
                    raise FileNotFoundError(
                        f"Credentials file not found: {self.credentials_path}\n"
                        f"Download OAuth credentials from Google Cloud Console"
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path),
                    self.scopes
                )
                # Manual auth flow for WSL/headless environments
                flow.redirect_uri = 'http://localhost:8080/'
                auth_url, _ = flow.authorization_url(prompt='consent')
                print("\n" + "="*60)
                print("CALENDAR OAUTH AUTHORIZATION")
                print("="*60)
                print("\nPlease visit this URL in your browser:")
                print(f"\n{auth_url}\n")
                print("After authorizing, you'll be redirected to a URL.")
                print("Copy the ENTIRE redirect URL and paste it below.\n")
                redirect_response = input("Paste redirect URL here: ").strip()
                flow.fetch_token(authorization_response=redirect_response)
                creds = flow.credentials
                logger.info("Obtained new calendar credentials via OAuth flow")
            
            # Save credentials
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
            logger.info(f"Saved calendar token to {self.token_file}")
        
        # Build service
        try:
            self.service = build('calendar', 'v3', credentials=creds, cache_discovery=False)
            logger.info("Calendar service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to build calendar service: {e}")
            raise
    
    def get_events_for_next_24_hours(
        self, 
        timezone_str: str = TIMEZONE_DEFAULT
    ) -> List[Dict]:
        """
        Fetch calendar events for the next 24 hours
        
        Args:
            timezone_str: Timezone string (e.g. "Europe/London")
        
        Returns:
            List of event dictionaries with simplified info
        """
        if not self.service:
            raise RuntimeError("Calendar service not initialized")
        
        try:
            # Get timezone
            tz = pytz.timezone(timezone_str)
            now = datetime.now(tz)
            end_time = now + timedelta(hours=24)
            
            # Format for API
            time_min = now.isoformat()
            time_max = end_time.isoformat()
            
            logger.info(
                f"Fetching events from {now.strftime('%Y-%m-%d %H:%M')} "
                f"to {end_time.strftime('%Y-%m-%d %H:%M')} ({timezone_str})"
            )
            
            # Call Calendar API
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime',
                timeZone=timezone_str
            ).execute()
            
            events = events_result.get('items', [])
            logger.info(f"Retrieved {len(events)} events")
            
            # Simplify event data
            simplified_events = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                
                simplified_events.append({
                    'start_time': start,
                    'end_time': end,
                    'summary': event.get('summary', '(No title)'),
                    'location': event.get('location', '')
                })
            
            return simplified_events
            
        except HttpError as error:
            logger.error(f"Calendar API error: {error}")
            raise
        except Exception as e:
            logger.error(f"Failed to fetch calendar events: {e}")
            raise
    
    def create_event(self, event_details: Dict) -> Dict:
        """
        Create a new calendar event (stub for future implementation)
        
        Args:
            event_details: Event specification dict with:
                - summary (str): Event title
                - start (str): ISO timestamp
                - end (str): ISO timestamp
                - location (str, optional)
                - description (str, optional)
        
        Returns:
            Created event dict
        """
        if not self.service:
            raise RuntimeError("Calendar service not initialized")
        
        try:
            event = self.service.events().insert(
                calendarId='primary',
                body=event_details
            ).execute()
            
            logger.info(f"Created event: {event.get('summary')}")
            return event
            
        except HttpError as error:
            logger.error(f"Failed to create event: {error}")
            raise
