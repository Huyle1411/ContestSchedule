import requests
import json
import jsonschema
from jsonschema import validate
import datetime
from datetime import date


clist_schema = {
    "meta": {
        "limit": "int",
        "next": "",
        "offset": "int",
        "previous": "",
        "total_count": "int",
    },
    "objects": {
        "contest": [
            {
                "id": 0,
                "resource": "",
                "resource_id": 0,
                "host": "",
                "event": "",
                "start": "datetime",
                "end": "datetime",
                "parsed_at": "datetime",
                "duration": "datetime",
                "href": "",
                "problems": "",
            }
        ]
    },
}


def validate_json(json_data):
    try:
        validate(instance=json_data, schema=clist_schema)
    except jsonschema.exceptions.ValidationError as err:
        print("[ERROR] invalid json data, error code:", err)
        return False
    return True


def fetch_data():
    today = date.today()
    next_day = today + datetime.timedelta(weeks=1)
    print(today)
    print(next_day)

    # must be in format YYYY-MM-DD HH:MM
    start_date_contest = today.strftime("%Y-%m-%d %H:%M")
    end_date_contest = next_day.strftime("%Y-%m-%d %H:%M")
    print("today is ", start_date_contest)

    api_key = "2ca91832af218083a3e9ac413cdb2bbd4614e887"
    username = "Bingoblin"
    url = "https://clist.by:443/api/v2/contest/"
    response = requests.get(
        url,
        params={
            "username": username,
            "api_key": api_key,
            "format": "json",
            "upcomming": "true",
            "order_by": "start",
            "start__gt": start_date_contest,
            "start__lt": end_date_contest,
        },
    )

    if response.status_code != 200:
        print("[ERROR] fetch error: ", response.status_code)
        return

    json_data = response.json()

    if not validate_json(json_data):
        return

    return json_data


def main():
    data = fetch_data()
    if data is None:
        print("Invalid data")
    else:
        print("Valid data")


if __name__ == "__main__":
    main()
