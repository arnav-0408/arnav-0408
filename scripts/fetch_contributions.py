import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup


# =========================================================
# SETTINGS
# =========================================================

USERNAME = "arnav-0408"

URL = f"https://github.com/users/{USERNAME}/contributions"

OUTPUT_FILE = Path("data/contributions.json")


# =========================================================
# FETCH GITHUB CONTRIBUTION PAGE
# =========================================================

response = requests.get(
    URL,
    headers={
        "User-Agent": "Mozilla/5.0",
        "Referer": f"https://github.com/{USERNAME}",
        "X-Requested-With": "XMLHttpRequest",
    },
    timeout=30,
)

response.raise_for_status()

soup = BeautifulSoup(
    response.text,
    "html.parser"
)


# =========================================================
# CONTRIBUTION CELLS
# =========================================================

cells = soup.select(
    ".js-calendar-graph-table "
    ".ContributionCalendar-day[data-date]"
)

print(
    f"Found {len(cells)} contribution cells"
)

if not cells:
    raise RuntimeError(
        "No contribution cells found."
    )


# =========================================================
# TOOLTIP MAP
# =========================================================
#
# GitHub structure:
#
# <td
#     id="contribution-day-component-..."
#     data-date="2026-08-23"
#     data-level="4">
# </td>
#
# <tool-tip
#     for="contribution-day-component-...">
#     15 contributions on August 23rd.
# </tool-tip>
#
# =========================================================

tooltip_map = {}

for tooltip in soup.select(
    ".js-calendar-graph tool-tip"
):

    tooltip_for = tooltip.get("for")

    if tooltip_for:
        tooltip_map[tooltip_for] = tooltip


print(
    f"Found {len(tooltip_map)} contribution tooltips"
)


# =========================================================
# EXTRACT DAYS
# =========================================================

days = []

for cell in cells:

    date = cell.get("data-date")

    cell_id = cell.get("id")

    if not date:
        continue

    count = 0

    tooltip = tooltip_map.get(cell_id)

    if tooltip:

        # Get ONLY the direct text inside tool-tip.
        text = tooltip.get_text(
            " ",
            strip=True
        )

        # Examples:
        #
        # 15 contributions on August 23rd.
        # 1 contribution on February 13th.
        # No contributions on August 24th.
        #
        match = re.match(
            r"(\d[\d,]*)\s+contribution",
            text,
            re.IGNORECASE
        )

        if match:

            count = int(
                match.group(1)
                .replace(",", "")
            )

    days.append(
        {
            "date": date,
            "count": count,
        }
    )


# =========================================================
# REMOVE DUPLICATE DATES
# =========================================================

unique_days = {}

for day in days:

    unique_days[
        day["date"]
    ] = day["count"]


days = [
    {
        "date": date,
        "count": count,
    }
    for date, count in sorted(
        unique_days.items()
    )
]


# =========================================================
# VALIDATE DATA
# =========================================================

total = sum(
    day["count"]
    for day in days
)

print(
    f"Total contributions found: {total}"
)


# NEVER OVERWRITE GOOD DATA WITH ZERO
if total == 0:

    raise RuntimeError(
        "ERROR: GitHub returned 0 contributions. "
        "Existing data was NOT overwritten."
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


today = datetime.now(
    timezone.utc
).date()


current_streak = 0


while day_map.get(
    today,
    0
) > 0:

    current_streak += 1

    today -= timedelta(
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
