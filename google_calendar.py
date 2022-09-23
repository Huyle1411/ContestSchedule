from __future__ import print_function

import datetime
import os.path
import logging
import pytz

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
        filename="/home/huyle/log/contest_schedule.txt",
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
        now = (
            datetime.datetime.combine(
                datetime.date.today(), datetime.datetime.min.time()
            )
            .utcnow()
            .isoformat()
            + "Z"
        )  # 'Z' indicates UTC time
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


def check_same_contest(contest, exist_contest):
    if not contest or not exist_contest:
        logging.error("Invalid contest!!! Return")
        return False

    result = True
    if str(contest["id"]) != str(exist_contest["id"]):
        logging.info("Not match - id1: %s, id2: %s", contest["id"], exist_contest["id"])
        result = False

    if contest["event"] != exist_contest["summary"]:
        logging.info(
            "Not match - summary1: %s, summary2: %s",
            contest["summary"],
            exist_contest["summary"],
        )
        result = False

    format_dt = "%Y-%m-%dT%H:%M:%S"
    format_utc = "%Y-%m-%dT%H:%M:%S%z"
    start_contest = datetime.datetime.strptime(contest["start"], format_dt)
    start_exist_contest = datetime.datetime.strptime(
        exist_contest["start"]["dateTime"], format_utc
    )
    start_contest = pytz.utc.localize(start_contest)
    if start_contest != start_exist_contest:
        logging.info(
            "Not match - start_contest: %s, start_exist_contest: %s",
            start_contest,
            start_exist_contest,
        )
        result = False

    end_contest = datetime.datetime.strptime(contest["end"], format_dt)
    end_exist_contest = datetime.datetime.strptime(
        exist_contest["end"]["dateTime"], format_utc
    )
    end_contest = pytz.utc.localize(end_contest)
    if end_contest != end_exist_contest:
        logging.info(
            "Not match - end_contest: %s, end_exist_contest: %s",
            end_contest,
            end_exist_contest,
        )
        result = False

    return result


def create_event_contest(service):
    # fetch contest data from clist
    contest_info = fetch_data.get_data_as_dict()
    if contest_info is None:
        logging.error("Data Error")
        return

    calendar_events = get_upcomming_event(service)

    # create event to calendar
    for contest in contest_info:
        match_id = False
        match_contest = False
        color_id = fetch_data.favorite_contests.index(contest["host"]) + 1
        event_calendar = {
            "id": contest["id"],
            "summary": contest["event"],
            "start": {"dateTime": contest["start"] + ".000000Z"},
            "end": {"dateTime": contest["end"] + ".000000Z"},
            "reminders": {
                "useDefault": False,
                "overrides": [{"method": "popup", "minutes": 30}],
            },
            "source": {
                "url": contest["href"],
                "title": contest["event"],
            },
            "colorId": str(color_id),
        }
        if not calendar_events:
            logging.info("Skip check duplicate events...")
        else:
            for exist_contest in calendar_events:
                if exist_contest["id"] == str(contest["id"]):
                    logging.info("Found match id in calendar")
                    match_id = True
                    match_contest = check_same_contest(contest, exist_contest)
                    break

        try:
            if not match_id:
                service.events().insert(
                    calendarId="primary", body=event_calendar
                ).execute()

                logging.info("Event created")
            elif not match_contest:
                service.events().patch(
                    calendarId="primary",
                    eventId=exist_contest["id"],
                    body=event_calendar,
                ).execute()

                logging.info("Event updated")
            else:
                logging.info("Completely match, no need to update")

        except HttpError as error:
            logging.error("An error occurred: %s" % error)


def main():
    init_log_config()
    service = create_service()
    create_event_contest(service)


if __name__ == "__main__":
    main()
