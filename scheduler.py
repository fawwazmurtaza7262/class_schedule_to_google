# important libraries
import csv              
import os               
import json             
import hashlib         
import sys              
from datetime import datetime, timedelta  

# Google authentication and API libraries
from google.oauth2.credentials import Credentials            
from google_auth_oauthlib.flow import InstalledAppFlow       
from google.auth.transport.requests import Request           
from googleapiclient.discovery import build                  
from googleapiclient.errors import HttpError                 
# ===================== CONSTANTS =====================
SCOPES = ["https://www.googleapis.com/auth/calendar"]
# OAuth scope allowing full access to Google Calendar

CONFIG_FILE = "config.json"
# Configuration file containing term dates, timezone, calendar ID, etc.

TOKEN_FILE = "token.json"
# Stores the user's OAuth access and refresh tokens

CREDENTIALS_FILE = "credentials.json"
# OAuth client credentials downloaded from Google Cloud Console

# Config loader
def load_config():
    if not os.path.exists(CONFIG_FILE):
        print(f"Configuration file '{CONFIG_FILE}' not found.")
        sys.exit(1)
    
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)
    