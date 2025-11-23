"""
Email Service - Gmail Integration
Handles OAuth 2.0 authentication and email retrieval for JARVIS
"""
import logging
import os
import base64
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import dateparser

# Allow insecure transport for localhost OAuth (development only)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Import config
from core.config import (
    SCOPES_GMAIL,
    GMAIL_TOKEN_FILE,
    CREDENTIALS_FILE,
    EMAIL_SNIPPET_MAX_LENGTH
)

logger = logging.getLogger(__name__)


class EmailService:
    """Gmail integration for JARVIS"""
    
    def __init__(self, credentials_path: Optional[Path] = None):
        """
        Initialize Email Service
        
        Args:
            credentials_path: Path to OAuth credentials.json
                            (defaults to config.CREDENTIALS_FILE)
        """
        self.credentials_path = credentials_path or CREDENTIALS_FILE
        self.token_file = GMAIL_TOKEN_FILE
        self.scopes = SCOPES_GMAIL
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Handle OAuth 2.0 authentication with Gmail"""
        creds = None
        
        # Load existing token
        if self.token_file.exists():
            try:
                creds = Credentials.from_authorized_user_file(
                    str(self.token_file),
                    self.scopes
                )
                logger.info("Loaded existing Gmail credentials")
            except Exception as e:
                logger.warning(f"Failed to load Gmail token: {e}")
        
        # Refresh or obtain new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    logger.info("Refreshed Gmail credentials")
                except Exception as e:
                    logger.error(f"Failed to refresh token: {e}")
                    creds = None
            
            if not creds:
                if not self.credentials_path.exists():
                    raise FileNotFoundError(
                        f"Credentials file not found: "
                        f"{self.credentials_path}"
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path),
                    self.scopes
                )
                # Manual auth flow for WSL/headless environments
                flow.redirect_uri = 'http://localhost:8080/'
                auth_url, _ = flow.authorization_url(prompt='consent')
                print("\n" + "="*60)
                print("GMAIL OAUTH AUTHORIZATION")
                print("="*60)
                print("\nPlease visit this URL in your browser:")
                print(f"\n{auth_url}\n")
                print("After authorizing, you'll be redirected to a URL.")
                print("Copy the ENTIRE redirect URL and paste it below.\n")
                redirect_response = input("Paste redirect URL here: ").strip()
                flow.fetch_token(authorization_response=redirect_response)
                creds = flow.credentials
                logger.info("Obtained new email credentials via OAuth flow")
            
            # Save credentials
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
            logger.info(f"Saved Gmail token to {self.token_file}")
        
        # Build service
        try:
            self.service = build('gmail', 'v1', credentials=creds, cache_discovery=False)
            logger.info("Gmail service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to build Gmail service: {e}")
            raise
    
    def get_unread_emails_since(
        self,
        time_ago: str,
        max_results: int = 20
    ) -> List[Dict]:
        """
        Fetch unread emails from a specific time window
        
        Args:
            time_ago: Human-readable time string (e.g. "1 hour", "24 hours")
            max_results: Maximum number of emails to return
        
        Returns:
            List of email dictionaries with simplified info
        """
        if not self.service:
            raise RuntimeError("Gmail service not initialized")
        
        try:
            # Parse time window
            cutoff_time = dateparser.parse(
                f"{time_ago} ago",
                settings={'TIMEZONE': 'UTC'}
            )
            if not cutoff_time:
                raise ValueError(f"Could not parse time: {time_ago}")
            
            # Convert to Unix timestamp for Gmail query
            after_timestamp = int(cutoff_time.timestamp())
            
            # Build query
            query = f"is:unread after:{after_timestamp}"
            
            logger.info(f"Fetching unread emails since {time_ago} ago")
            
            # Call Gmail API
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            logger.info(f"Found {len(messages)} unread emails")
            
            # Fetch message details
            emails = []
            priority_labels = {'Action', 'Meeting', 'IMPORTANT'}
            
            for msg in messages:
                try:
                    message = self.service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='metadata',
                        metadataHeaders=['From', 'Subject']
                    ).execute()
                    
                    headers = message.get('payload', {}).get('headers', [])
                    subject = next(
                        (h['value'] for h in headers if h['name'] == 'Subject'),
                        '(No subject)'
                    )
                    sender = next(
                        (h['value'] for h in headers if h['name'] == 'From'),
                        '(Unknown sender)'
                    )
                    
                    snippet = message.get('snippet', '')
                    if len(snippet) > EMAIL_SNIPPET_MAX_LENGTH:
                        snippet = snippet[:EMAIL_SNIPPET_MAX_LENGTH] + '...'
                    
                    labels = message.get('labelIds', [])
                    
                    # Check for priority labels
                    has_priority = bool(
                        set(labels) & priority_labels
                    )
                    
                    emails.append({
                        'subject': subject,
                        'sender': sender,
                        'snippet': snippet,
                        'labels': labels,
                        'priority': has_priority
                    })
                    
                except Exception as e:
                    logger.warning(f"Failed to fetch message {msg['id']}: {e}")
                    continue
            
            # Sort: priority first, then by order received
            emails.sort(key=lambda x: (not x['priority']))
            
            logger.info(
                f"Retrieved {len(emails)} emails, "
                f"{sum(1 for e in emails if e['priority'])} priority"
            )
            
            return emails
            
        except HttpError as error:
            logger.error(f"Gmail API error: {error}")
            raise
        except Exception as e:
            logger.error(f"Failed to fetch emails: {e}")
            raise
