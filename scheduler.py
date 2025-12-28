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