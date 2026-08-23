import json
import re
from datetime import datetime, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USERNAME = "arnav-0408"
URL = f"https://github.com/users/{USERNAME}/contributions"

response = requests.get(
    URL,
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=30
)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

days = []

for cell in soup.select("[data-date]"):
    date = cell.get("data-date")

    if not date:
        continue

    text = cell.get_text(" ", strip=True)

    match = re.search(r"(\d[\d,]*) contribution", text)
    count = int(match.group(1).replace(",", "")) if match else 0

    days.append({
        "date": date,
        "count": count
    })

days.sort(key=lambda x: x["date"])

# Remove duplicate dates
unique_days = {}

for day in days:
    unique_days[day["date"]] = day["count"]

days = [
    {"date": date, "count": count}
    for date, count in sorted(unique_days.items())
]

# Total contributions
total = sum(day["count"] for day in days)

# Best day
best_day = max(days, key=lambda x: x["count"], default=None)

# Current streak
current_streak = 0

if days:
    today = datetime.utcnow().date()

    for day in reversed(days):
        date = datetime.strptime(day["date"], "%Y-%m-%d").date()

        if date > today:
            continue

        if day["count"] > 0:
            current_streak += 1
            today -= timedelta(days=1)
        else:
            break

# Longest streak
longest_streak = 0
streak = 0
previous_date = None

for day in days:
    date = datetime.strptime(day["date"], "%Y-%m-%d").date()

    if day["count"] > 0:
        if previous_date and date == previous_date + timedelta(days=1):
            streak += 1
        else:
            streak = 1

        longest_streak = max(longest_streak, streak)
    else:
        streak = 0

    previous_date = date

data = {
    "username": USERNAME,
    "generated_at": datetime.utcnow().isoformat() + "Z",
    "total_contributions": total,
    "current_streak": current_streak,
    "longest_streak": longest_streak,
    "best_day": best_day,
    "days": days
}

output = Path("data/contributions.json")
output.parent.mkdir(parents=True, exist_ok=True)

output.write_text(
    json.dumps(data, indent=2),
    encoding="utf-8"
)

print(f"Fetched {len(days)} days")
print(f"Total contributions: {total}")
print(f"Current streak: {current_streak}")
print(f"Longest streak: {longest_streak}")
