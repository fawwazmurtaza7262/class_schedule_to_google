# ===================== IMPORTS =====================
# Built-in modules
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


# ===================== CONFIG LOADER =====================
def load_config():
    """
    Loads configuration settings from config.json.
    Exits the program if the file does not exist.
    """
    if not os.path.exists(CONFIG_FILE):
        print(f"Error: {CONFIG_FILE} not found. Please create it using the template.")
        sys.exit(1)

    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)


# ===================== DAY MAPPING =====================
# Converts weekday names to Python's weekday integers
# Monday = 0, Sunday = 6
DAY_TO_INT = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2, 
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6
}


# ===================== GOOGLE CALENDAR AUTH =====================
def get_calendar_service():
    """
    Authenticates the user with Google OAuth and
    returns a Google Calendar service object.
    """
    creds = None

    # Load saved credentials if they exist
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # If credentials are missing or invalid
    if not creds or not creds.valid:

        # Attempt token refresh if possible
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                # If refresh fails, delete token and restart auth
                os.remove(TOKEN_FILE)
                return get_calendar_service()
        else:
            # If no credentials exist, start OAuth login flow
            if not os.path.exists(CREDENTIALS_FILE):
                print(f"Error: {CREDENTIALS_FILE} is missing.")
                print("Please download your OAuth credentials from Google Cloud Console.")
                sys.exit(1)

            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE,
                SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save credentials for future runs
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    # Build and return the Google Calendar API service
    return build("calendar", "v3", credentials=creds)


# ===================== DATE CALCULATIONS =====================
def calculate_first_occurrence(term_start_str, weekday_name):
    """
    Given a term start date and weekday name,
    returns the first date that falls on that weekday.
    """
    # Convert term start date string to date object
    term_start = datetime.strptime(term_start_str, "%Y-%m-%d").date()

    # Convert weekday name to integer
    target_int = DAY_TO_INT.get(weekday_name)
    if target_int is None:
        raise ValueError(f"Invalid day name: {weekday_name}")

    # Calculate offset in days to the target weekday
    delta = (target_int - term_start.weekday()) % 7
    return term_start + timedelta(days=delta)


# ===================== EVENT ID GENERATION =====================
def generate_event_id(course_code, session_type, day, start_time):
    """
    Generates a deterministic Google Calendar event ID.
    Prevents duplicate event creation.
    """
    raw_id = f"{course_code}-{session_type}-{day}-{start_time}"
    hashed = hashlib.sha1(raw_id.encode('utf-8')).hexdigest()

    # Google Calendar requires lowercase alphanumeric IDs
    return f"cls{hashed[:20]}"


# ===================== MAIN PROGRAM =====================
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
                first_date = calculate_first_occurrence(term_start, day)

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
