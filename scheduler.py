import csv              # For reading the schedule CSV file
import os               # For file existence checks
import json             # For loading configuration data
import hashlib          # For generating stable unique event IDs
import sys              # For exiting the program on fatal errors
from datetime import datetime, timedelta  # For date and time calculations

# Google authentication and API libraries
from google.oauth2.credentials import Credentials            # Handles OAuth credentials
from google_auth_oauthlib.flow import InstalledAppFlow       # OAuth login flow
from google.auth.transport.requests import Request           # Token refresh requests
from googleapiclient.discovery import build                  # Builds Google API service
from googleapiclient.errors import HttpError                 # Handles API errors

# ===================== CONSTANTS =====================
SCOPES = ["https://www.googleapis.com/auth/calendar"]
# OAuth scope allowing full access to Google Calendar

CONFIG_FILE = "config.json"
# Configuration file containing term dates, timezone, calendar ID, etc.

TOKEN_FILE = "token.json"
# Stores the user's OAuth access and refresh tokens

CREDENTIALS_FILE = "credentials.json"
# OAuth client credentials downloaded from Google Cloud Console