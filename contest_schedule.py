from __future__ import print_function

import datetime
import os.path
from logger import logger
import pytz

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


import fetch_data

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]
PATH_CREDENTIALS = "/home/huyle/automation/creds_google_api/"


def create_service():
    logger.info("check credentials")
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(PATH_CREDENTIALS + "token.json"):
        creds = Credentials.from_authorized_user_file(
            PATH_CREDENTIALS + "token.json", SCOPES
        )
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                PATH_CREDENTIALS + "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(PATH_CREDENTIALS + "token.json", "w") as token:
            token.write(creds.to_json())

    if creds is None:
        logger.error("Failed to create credentials")
        return

    try:
        service = build("calendar", "v3", credentials=creds)
    except HttpError as error:
        logger.error("An error occurred: %s" % error)

    return service


def get_calendar_id(service):
    page_token = None
    while True:
        calendar_list = service.calendarList().list(pageToken=page_token).execute()
        for calendar_list_entry in calendar_list["items"]:
            if calendar_list_entry["summary"] == "Programming":
                logger.info("Found calendar id: %s", calendar_list_entry["id"])
                return calendar_list_entry["id"]
        page_token = calendar_list.get("nextPageToken")
        if not page_token:
            break

    logger.error("Not found calendar id Return default id primary")
    return "primary"


def get_upcomming_event(service, calendar_id):
    if service is None:
        logger.error("Something wrong @@@ Return")

    try:
        now = (
            datetime.datetime.combine(
                datetime.date.today(), datetime.datetime.min.time()
            )
            .utcnow()
            .isoformat()
            + "Z"
        )  # 'Z' indicates UTC time
        logger.info("Getting the upcoming events")
        events_result = (
            service.events()
            .list(
                calendarId=calendar_id,
                timeMin=now,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])

        if not events:
            logger.info("No upcoming events found.")
            return

    except HttpError as error:
        logger.error("An error occurred: %s" % error)

    return events


def check_same_contest(contest, exist_contest):
    if not contest or not exist_contest:
        logger.error("Invalid contest!!! Return")
        return False

    result = True
    try:
        if str(contest["id"]) != str(exist_contest["id"]):
            logger.info(
                "Not match - contest id: %s, exist contest id: %s",
                contest["id"],
                exist_contest["id"],
            )
            result = False

        if contest["event"] != exist_contest["summary"]:
            logger.info(
                "Not match - contest summary: %s, exist contest summary: %s",
                contest["event"],
                exist_contest["summary"],
            )
            result = False

        if contest["href"] != exist_contest["description"]:
            logger.info(
                "Not match - contest description: %s, exist contest description: %s",
                contest["href"],
                exist_contest["description"],
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
            logger.info(
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
            logger.info(
                "Not match - end_contest: %s, end_exist_contest: %s",
                end_contest,
                end_exist_contest,
            )
            result = False
    except KeyError:
        logger.debug("Invalid key, return false")
        result = False

    return result


def get_color(contest_host):
    if contest_host is None:
        logger.error("Invalid contest host, return default color id")
        return 1
    for idx, item in enumerate(fetch_data.favorite_contests):
        if item in contest_host:
            return idx + 1
    logger.info("No match found, return default color id")
    return 1


def create_event_contest(service):
    # fetch contest data from clist
    contest_info = fetch_data.get_data_as_dict()
    if contest_info is None:
        logger.error("Data Error")
        return

    calendar_id = get_calendar_id(service)
    calendar_events = get_upcomming_event(service, calendar_id)

    # create event to calendar
    for contest in contest_info:
        match_id = False
        match_contest = False
        color_id = get_color(contest["host"])
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
            "description": contest["href"],
            "colorId": str(color_id),
        }
        if not calendar_events:
            logger.info("Skip check duplicate events...")
        else:
            for exist_contest in calendar_events:
                if exist_contest["id"] == str(contest["id"]):
                    logger.info("Found match id in calendar")
                    match_id = True
                    match_contest = check_same_contest(contest, exist_contest)
                    break

        try:
            if not match_id:
                service.events().insert(
                    calendarId=calendar_id, body=event_calendar
                ).execute()

                logger.info("Event created %s", contest["event"])
            elif not match_contest:
                service.events().patch(
                    calendarId=calendar_id,
                    eventId=exist_contest["id"],
                    body=event_calendar,
                ).execute()

                logger.info("Event updated %s", contest["event"])
            else:
                logger.info("Completely match, no need to update %s", contest["event"])

        except HttpError as error:
            logger.error("An error occurred: %s" % error)


def main():
    # init_log_config()
    service = create_service()
    create_event_contest(service)


if __name__ == "__main__":
    main()
