import requests
import json
import jsonschema
from jsonschema import validate
import datetime
from datetime import date
from logger import logger


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

favorite_contests = [
    "codeforces.com",
    "atcoder.jp",
    "codechef.com",
    "codingcompetitions.withgoogle.com",
    "facebook.com",
    "leetcode.com",
]


def validate_json(json_data):
    logger.info("validate json data")
    try:
        validate(instance=json_data, schema=clist_schema)
    except jsonschema.exceptions.ValidationError as err:
        logger.error(f"invalid json data, error code: {err}")
        return False
    return True


def get_data_as_dict():
    logger.info("start getting data from clist...")
    today = date.today()
    next_day = today + datetime.timedelta(weeks=1)
    logger.info(f"get info from {today} to {next_day}")

    # must be in format YYYY-MM-DD HH:MM
    start_date_contest = today.strftime("%Y-%m-%d %H:%M")
    end_date_contest = next_day.strftime("%Y-%m-%d %H:%M")

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
        logger.error(f"fetch error: {response.status_code}")
        return

    json_data = response.json()

    # logger.debug(json.dumps(json_data, indent=2))

    if not validate_json(json_data):
        return

    result_dict = [
        item
        for item in json_data["objects"]
        if any(fav in item["host"] for fav in favorite_contests)
        # if any(item["host"] in fav for fav in favorite_contests)
    ]

    logger.debug(json.dumps(result_dict, indent=2))

    return result_dict
