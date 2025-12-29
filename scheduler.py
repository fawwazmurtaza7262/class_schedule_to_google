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


DAY_TO_INT = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6
}

def get_calendar_service():
    creds = None
    
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                os.remove(TOKEN_FILE)
                return get_calendar_service()
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                print(f"Credentials file '{CREDENTIALS_FILE}' not found.")
                print("Please download your OAuth credintials from Google Cloud Console.")
                sys.exit(1)
        
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
        
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
        
    return build("calendar", "v3", credentials=creds)


def calculate_first_occurence(term_start_str, weekday_name):
    term_start = datetime.strptime(term_start_str, "%Y-%m-%d").date()
    
    target_weekday = DAY_TO_INT.get(weekday_name)
    if target_weekday is None:
        raise ValueError(f"Invalid weekday name: {weekday_name}")
    
    delta_days = {target_weekday - term_start.weekday()} % 7
    return term_start + timedelta(days=delta_days)




    
                