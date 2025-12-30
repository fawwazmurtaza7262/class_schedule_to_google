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

def generate_event_id(course_id, session_type, day, start_time):
    raw_id = f"{course_id} - {session_type} - {day} - {start_time}"
    hashed = hashlib.md5(raw_id.encode().hexdigest())
    return f"cls{hashed[:20]}"

def main():
    # Load configuration settings
    config = load_config()

    # Get CSV file path from config or use default
    csv_path = config.get("csv_filename", "schedule.csv")

    # Ensure CSV file exists
    if not os.path.exists(csv_path):
        print(f"Error: CSV file '{csv_path}' not found.")
        return

    # Authenticate with Google Calendar
    print("Authenticating with Google...")
    service = get_calendar_service()

    # Parse academic term start and end dates
    term_start = config["term_start_date"]
    term_end = datetime.strptime(config["term_end_date"], "%Y-%m-%d")

    # Create recurrence UNTIL date (inclusive)
    recurrence_end = (term_end + timedelta(days=1)).strftime("%Y%m%dT000000Z")

    # Load timezone and calendar ID
    timezone = config.get("timezone", "America/Toronto")
    calendar_id = config.get("calendar_id", "primary")

    print(f"Reading {csv_path}...")

    # Open and read the CSV file
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        # Required CSV headers
        required_headers = [
            "Course Name",
            "Course Code",
            "Day",
            "Start Time",
            "End Time",
            "Location"
        ]

        # Validate CSV structure
        if not all(h in reader.fieldnames for h in required_headers):
            print(f"Error: CSV is missing required columns: {required_headers}")
            return

        # Process each row in the CSV
        for row in reader:

            # Extract and clean row values
            name = row["Course Name"].strip()
            code = row["Course Code"].strip()
            day = row["Day"].strip()
            start_str = row["Start Time"].strip()
            end_str = row["End Time"].strip()
            loc = row["Location"].strip()

            # Determine session type based on course name
            session_type = "Lecture"
            if "lab" in name.lower():
                session_type = "Lab"
            elif "tutorial" in name.lower():
                session_type = "Tutorial"

            # Calculate the first event date and time
            try:
                first_date = calculate_first_occurence(term_start, day)

                start_dt = datetime.combine(
                    first_date,
                    datetime.strptime(start_str, "%I:%M %p").time()
                )
                end_dt = datetime.combine(
                    first_date,
                    datetime.strptime(end_str, "%I:%M %p").time()
                )
            except ValueError:
                # Skip rows with invalid date or time formats
                print(f"Skipping row due to time format error: {row}")
                continue

            # Build Google Calendar event payload
            event_body = {
                "summary": f"{code} – {name} ({session_type})",
                "location": loc,
                "description": f"Session: {session_type}\nCourse: {name}",
                "start": {
                    "dateTime": start_dt.strftime("%Y-%m-%dT%H:%M:%S"),
                    "timeZone": timezone,
                },
                "end": {
                    "dateTime": end_dt.strftime("%Y-%m-%dT%H:%M:%S"),
                    "timeZone": timezone,
                },
                "recurrence": [
                    f"RRULE:FREQ=WEEKLY;UNTIL={recurrence_end}"
                ],
                "id": generate_event_id(code, session_type, day, start_str)
            }

            # Insert event into Google Calendar
            try:
                service.events().insert(
                    calendarId=calendar_id,
                    body=event_body
                ).execute()

                print(f"Created: {code} ({session_type}) on {day}")

            except HttpError as e:
                # Handle duplicate event errors
                if e.resp.status == 409:
                    print(f"Skipped (Exists): {code} ({session_type})")
                else:
                    print(f"Error creating {code}: {e}")

    print("\nImport complete!")


# ===================== ENTRY POINT =====================
if __name__ == "__main__":
    main()





    
                