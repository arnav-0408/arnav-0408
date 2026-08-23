import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests


# =========================================================
# SETTINGS
# =========================================================

USERNAME = "arnav-0408"

OUTPUT_FILE = Path(
    "data/contributions.json"
)

GRAPHQL_URL = "https://api.github.com/graphql"

TOKEN = os.getenv("GH_TOKEN")


# =========================================================
# CHECK TOKEN
# =========================================================

if not TOKEN:
    raise RuntimeError(
        "GH_TOKEN is not set."
    )


# =========================================================
# GRAPHQL QUERY
# =========================================================

QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
    user(login: $login) {
        contributionsCollection(
            from: $from
            to: $to
        ) {
            contributionCalendar {
                totalContributions

                weeks {
                    contributionDays {
                        date
                        contributionCount
                        weekday
                    }
                }
            }

            restrictedContributionsCount
        }
    }
}
"""


# =========================================================
# DATE RANGE
# =========================================================

today = datetime.now(
    timezone.utc
).date()

end_date = today + timedelta(
    days=1
)

start_date = end_date - timedelta(
    days=365
)

from_datetime = (
    f"{start_date.isoformat()}T00:00:00Z"
)

to_datetime = (
    f"{end_date.isoformat()}T00:00:00Z"
)


# =========================================================
# REQUEST
# =========================================================

response = requests.post(
    GRAPHQL_URL,

    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "arnav-contribution-heatmap",
    },

    json={
        "query": QUERY,

        "variables": {
            "login": USERNAME,
            "from": from_datetime,
            "to": to_datetime,
        },
    },

    timeout=30,
)

response.raise_for_status()

result = response.json()


# =========================================================
# GRAPHQL ERRORS
# =========================================================

if "errors" in result:

    print(
        json.dumps(
            result["errors"],
            indent=2
        )
    )

    raise RuntimeError(
        "GitHub GraphQL API returned an error."
    )


# =========================================================
# GET USER DATA
# =========================================================

user = result["data"]["user"]

if not user:

    raise RuntimeError(
        f"GitHub user '{USERNAME}' "
        "was not found."
    )


collection = (
    user["contributionsCollection"]
)

calendar = (
    collection["contributionCalendar"]
)


# =========================================================
# BUILD DAILY DATA
# =========================================================

days = []

for week in calendar["weeks"]:

    for day in week["contributionDays"]:

        days.append(
            {
                "date": day["date"],
                "count": day["contributionCount"],
            }
        )


days.sort(
    key=lambda x: x["date"]
)


# =========================================================
# TOTAL
# =========================================================

total = sum(
    day["count"]
    for day in days
)

api_total = (
    calendar["totalContributions"]
)


print(
    f"GraphQL total: {api_total}"
)

print(
    f"Calculated total: {total}"
)


# =========================================================
# VALIDATION
# =========================================================

if total == 0:

    raise RuntimeError(
        "GitHub API returned 0 contributions. "
        "Existing data was NOT overwritten."
    )

if total != api_total:

    raise RuntimeError(
        "Calculated contribution total does "
        "not match GitHub's calendar total."
    )


# =========================================================
# BEST DAY
# =========================================================

best_day = max(
    days,
    key=lambda x: x["count"],
    default=None
)


# =========================================================
# CURRENT STREAK
# =========================================================

day_map = {
    datetime.strptime(
        day["date"],
        "%Y-%m-%d"
    ).date(): day["count"]

    for day in days
}


current_date = today

current_streak = 0

while day_map.get(
    current_date,
    0
) > 0:

    current_streak += 1

    current_date -= timedelta(
        days=1
    )


# =========================================================
# LONGEST STREAK
# =========================================================

longest_streak = 0
streak = 0

for day in days:

    if day["count"] > 0:

        streak += 1

        longest_streak = max(
            longest_streak,
            streak
        )

    else:

        streak = 0


# =========================================================
# BUILD DATA
# =========================================================

data = {
    "username": USERNAME,

    "generated_at":
        datetime.now(
            timezone.utc
        ).isoformat(),

    "total_contributions":
        total,

    "current_streak":
        current_streak,

    "longest_streak":
        longest_streak,

    "best_day":
        best_day,

    "days":
        days,
}


# =========================================================
# SAVE
# =========================================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT_FILE.write_text(
    json.dumps(
        data,
        indent=2
    ),
    encoding="utf-8"
)


# =========================================================
# RESULT
# =========================================================

print()
print("=" * 60)
print("RESULT")
print("=" * 60)

print(
    f"Fetched {len(days)} days"
)

print(
    f"Total contributions: {total}"
)

print(
    f"Current streak: {current_streak}"
)

print(
    f"Longest streak: {longest_streak}"
)

if best_day:

    print(
        f'Best day: '
        f'{best_day["date"]} '
        f'({best_day["count"]} contributions)'
    )

print("=" * 60)
