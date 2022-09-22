from __future__ import print_function

import datetime
import os.path
import logging

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import fetch_data

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]


def init_log_config():
    logging.basicConfig(
        filename="contest_log",
        filemode="a",
        format="%(asctime)s [%(levelname)s][%(name)s]  %(message)s",
        datefmt="%H:%M:%S",
        level=logging.DEBUG,
    )


def create_service():
    logging.info("check credentials")
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    if creds is None:
        logging.error("Failed to create credentials")
        return

    try:
        service = build("calendar", "v3", credentials=creds)
    except HttpError as error:
        logging.error("An error occurred: %s" % error)

    return service


def get_upcomming_event(service):
    if service is None:
        logging.error("Something wrong @@@ Return")

    try:
        now = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
        logging.info("Getting the upcoming events")
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=now,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])

        if not events:
            logging.info("No upcoming events found.")
            return

    except HttpError as error:
        logging.error("An error occurred: %s" % error)

    return events


def create_event_contest(service):
    # fetch contest data from clist
    contest_info = fetch_data.get_data_as_dict()
    if contest_info is None:
        logging.error("Data Error")
        return

    calendar_events = get_upcomming_event(service)

    if not calendar_events:
        logging.info("Skip check duplicate events...")
    # else:
    # for new_contest in json_data:
    # check duplicate event

    # now = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
    # test_event = {
    #     "summary": "Hello World",
    #     "location": "Hanoi",
    #     "description": "Testing create event",
    #     "start": {
    #         "dateTime": start_time,
    #     },
    #     "end": {
    #         "dateTime": end_time,
    #     },
    #     "reminders": {
    #         "useDefault": False,
    #         "overrides": [
    #             {"method": "popup", "minutes": 5},
    #         ],
    #     },
    # }

    # create_event_result = (
    #     service.events().insert(calendarId="primary", body=test_event).execute()
    # )
    # logging.info("Event created: %s" % (create_event_result.get("htmlLink")))
    # print("Event created: %s" % (create_event_result.get("htmlLink")))

    # print("An error occurred: %s" % error)


def main():
    init_log_config()
    service = create_service()
    create_event_contest(service)


if __name__ == "__main__":
    main()
