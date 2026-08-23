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

OUTPUT = Path("data/contributions.json")


# =========================================================
# FETCH GITHUB PAGE
# =========================================================

response = requests.get(
    URL,
    headers={
        "User-Agent": "Mozilla/5.0",
        "Accept": "text/html",
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
# FIND CONTRIBUTION CELLS
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
        "Could not find GitHub contribution cells."
    )


# =========================================================
# FIND TOOLTIPS
# =========================================================

tooltips = {}

for tooltip in soup.select(
    ".js-calendar-graph tool-tip"
):

    tooltip_id = tooltip.get("for")

    if tooltip_id:
        tooltips[tooltip_id] = tooltip


print(
    f"Found {len(tooltips)} contribution tooltips"
)


# =========================================================
# EXTRACT DAILY CONTRIBUTIONS
# =========================================================

days = []

for cell in cells:

    date = cell.get("data-date")

    cell_id = cell.get("id")

    if not date:
        continue

    count = 0

    # -----------------------------------------------------
    # Method 1: matching tool-tip
    # -----------------------------------------------------

    tooltip = tooltips.get(cell_id)

    if tooltip:

        text = tooltip.get_text(
            " ",
            strip=True
        )

        match = re.search(
            r"(\d[\d,]*)\s+contribution",
            text,
            re.IGNORECASE
        )

        if match:

            count = int(
                match.group(1)
                .replace(",", "")
            )

    # -----------------------------------------------------
    # Method 2: fallback to cell attributes/text
    # -----------------------------------------------------

    if count == 0:

        possible_text = " ".join(
            [
                cell.get_text(
                    " ",
                    strip=True
                ),
                cell.get(
                    "aria-label",
                    ""
                ),
                cell.get(
                    "title",
                    ""
                ),
            ]
        )

        match = re.search(
            r"(\d[\d,]*)\s+contribution",
            possible_text,
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
# REMOVE DUPLICATES
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
# VALIDATION
# =========================================================

total = sum(
    day["count"]
    for day in days
)

print(
    f"Total contributions found: {total}"
)

if total == 0:

    raise RuntimeError(
        "GitHub returned contribution cells, "
        "but all contribution counts were 0. "
        "Refusing to overwrite existing data."
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

current_streak = 0

if days:

    today = datetime.now(
        timezone.utc
    ).date()

    day_map = {
        datetime.strptime(
            day["date"],
            "%Y-%m-%d"
        ).date(): day["count"]
        for day in days
    }

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

    count = day["count"]

    if count > 0:

        streak += 1

        longest_streak = max(
            longest_streak,
            streak
        )

    else:

        streak = 0


# =========================================================
# DATA
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

OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT.write_text(
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
print("=" * 50)
print("RESULT")
print("=" * 50)

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

print("=" * 50)
