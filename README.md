# Google Calendar Schedule Importer

- This is a Python script that imports a class schedule from a CSV file into Google Calendar and creates weekly recurring events for the full academic term.
- The script uses Google OAuth 2.0 for authentication and the Google Calendar API to create events while preventing duplicates.

## Features

- Imports schedules from a CSV file
- Creates weekly recurring Google Calendar events
- Supports lectures, labs, and tutorials
- Prevents duplicate events using deterministic event IDs
- Configurable term dates, timezone, and calendar

## Requirements

- Python 3.8+
- Google account
- Google Calendar API enabled

## Google API Setup

1. Go to Google Cloud Console
2. Create a new project
3. Enable **Google Calendar API**
4. Create an **OAuth Client ID**
   - Application type: Desktop App
5. Download the credentials file
6. Rename it to `credentials.json`

## Configuration (`config.json`)

Create a `config.json` file with the following parameters:

```json
{
  "csv_filename": "schedule.csv",
  "term_start_date": "YYYY-MM-DD",
  "term_end_date": "YYYY-MM-DD",
  "timezone": "your_timezone",
  "calendar_id": "primary"
}


