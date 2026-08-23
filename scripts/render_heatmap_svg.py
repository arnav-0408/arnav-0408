import json
from pathlib import Path

DATA_FILE = Path("data/contributions.json")
OUTPUT_FILE = Path("contrib-heatmap.svg")

WIDTH = 860
HEIGHT = 220

CELL = 11
GAP = 3

PALETTE = [
    "#161b22",
    "#0e4429",
    "#006d32",
    "#26a641",
    "#39d353",
    "#69f0a0",
]

data = json.loads(
    DATA_FILE.read_text(encoding="utf-8")
)

days = data["days"][-371:]

max_count = max(
    (d["count"] for d in days),
    default=1
)


def get_level(count):
    if count == 0:
        return 0

    ratio = count / max_count

    if ratio <= 0.2:
        return 1
    elif ratio <= 0.4:
        return 2
    elif ratio <= 0.6:
        return 3
    elif ratio <= 0.8:
        return 4
    else:
        return 5


# Split contribution data into weeks
weeks = [
    days[i:i + 7]
    for i in range(0, len(days), 7)
]


svg = [
    f'''<svg xmlns="http://www.w3.org/2000/svg"
    width="{WIDTH}"
    height="{HEIGHT}"
    viewBox="0 0 {WIDTH} {HEIGHT}">''',

    """
    <style>

        .cell {
            opacity: 0;
            animation: reveal 0.375s ease-out forwards;
        }

        @keyframes reveal {

            from {
                opacity: 0;
                transform: translateY(-5px);
            }

            to {
                opacity: 1;
                transform: translateY(0);
            }

        }

    </style>
    """,

    '<rect width="100%" height="100%" '
    'rx="12" fill="#0d1117"/>',

    '<text x="20" y="28" '
    'fill="#c9d1d9" '
    'font-family="monospace" '
    'font-size="16">'
    'arnav-0408 · contribution activity'
    '</text>'
]


START_X = 20
START_Y = 50


# =========================================================
# CONTRIBUTION CELLS
# =========================================================

for week_index, week in enumerate(weeks):

    for day_index, day in enumerate(week):

        x = (
            START_X
            + week_index * (CELL + GAP)
        )

        y = (
            START_Y
            + day_index * (CELL + GAP)
        )

        count = day["count"]

        level = get_level(count)

        color = PALETTE[level]

        # Faster staggered animation
        delay = (
            week_index * 0.0375
            + day_index * 0.0075
        )

        svg.append(
            f'<rect '
            f'class="cell" '
            f'x="{x}" '
            f'y="{y}" '
            f'width="{CELL}" '
            f'height="{CELL}" '
            f'rx="2" '
            f'fill="{color}" '
            f'style="animation-delay:{delay:.4f}s">'

            f'<title>'
            f'{day["date"]}: '
            f'{count} contributions'
            f'</title>'

            f'</rect>'
        )


# =========================================================
# STATISTICS
# =========================================================

total = data["total_contributions"]

current = data["current_streak"]

longest = data["longest_streak"]


svg.append(
    f'<text '
    f'x="20" '
    f'y="175" '
    f'fill="#8b949e" '
    f'font-family="monospace" '
    f'font-size="13">'

    f'{total:,} contributions · '

    f'current streak: '
    f'{current} days · '

    f'longest streak: '
    f'{longest} days'

    f'</text>'
)


# =========================================================
# LEGEND
# =========================================================

legend_x = WIDTH - 180
legend_y = 195


svg.append(
    f'<text '
    f'x="{legend_x - 40}" '
    f'y="{legend_y + 10}" '
    f'fill="#8b949e" '
    f'font-family="monospace" '
    f'font-size="11">'
    f'Less'
    f'</text>'
)


for i, color in enumerate(PALETTE):

    x = (
        legend_x
        + i * 20
    )

    svg.append(
        f'<rect '
        f'x="{x}" '
        f'y="{legend_y}" '
        f'width="12" '
        f'height="12" '
        f'rx="2" '
        f'fill="{color}"/>'
    )


svg.append(
    f'<text '
    f'x="{legend_x + 130}" '
    f'y="{legend_y + 10}" '
    f'fill="#8b949e" '
    f'font-family="monospace" '
    f'font-size="11">'
    f'More'
    f'</text>'
)


# =========================================================
# CLOSE SVG
# =========================================================

svg.append("</svg>")


# =========================================================
# WRITE FILE
# =========================================================

OUTPUT_FILE.write_text(
    "\n".join(svg),
    encoding="utf-8"
)

print(
    f"Created {OUTPUT_FILE}"
)
