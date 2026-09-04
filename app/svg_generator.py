from xml.sax.saxutils import escape


LANGUAGE_COLORS = {
    "Python": "#3572A5",
    "JavaScript": "#F1E05A",
    "TypeScript": "#3178C6",
    "C++": "#F34B7D",
    "C": "#555555",
    "HTML": "#E34C26",
    "CSS": "#563D7C",
    "Java": "#B07219",
    "Go": "#00ADD8",
    "Rust": "#DEA584",
    "PHP": "#4F5D95",
    "Ruby": "#701516",
    "Kotlin": "#A97BFF",
    "Swift": "#F05138",
}


def shorten(text: str, max_chars: int = 14) -> str:
    if len(text) > max_chars:
        return text[: max_chars - 3] + "..."
    return text


def format_bytes(num_bytes: int | None) -> str:
    if num_bytes is None:
        return "—"

    if num_bytes >= 1024**3:
        return f"{num_bytes / 1024**3:.1f} GB"

    if num_bytes >= 1024**2:
        return f"{num_bytes / 1024**2:.1f} MB"

    if num_bytes >= 1024:
        return f"{num_bytes / 1024:.1f} KB"

    return f"{num_bytes} B"


def generate_stats_svg(
    username: str,
    percentages: dict[str, float],
    total_bytes: int | None = None,
    repo_count: int | None = None,
    fetched_at: str | None = None,
) -> str:

    safe_username = escape(username)
    safe_fetched_at = escape(fetched_at) if fetched_at else "Recently"

    # Keep the card readable when there are many languages.
    languages = list(percentages.items())[:8]

    width = 700
    header_height = 125
    row_height = 48
    stats_height = 105
    footer_height = 55

    height = (
        header_height
        + len(languages) * row_height
        + stats_height
        + footer_height
    )

    svg = f"""\
<svg
    width="{width}"
    height="{height}"
    viewBox="0 0 {width} {height}"
    xmlns="http://www.w3.org/2000/svg"
>

    <rect
        width="100%"
        height="100%"
        rx="16"
        fill="#0d1117"
        stroke="#30363d"
        stroke-width="2"
    />

    <!-- Header -->
    <text
        x="35"
        y="48"
        fill="#f0f6fc"
        font-size="25"
        font-family="Arial, sans-serif"
        font-weight="700"
    >
        GitHub Language Stats
    </text>

    <text
        x="35"
        y="82"
        fill="#58a6ff"
        font-size="18"
        font-family="Arial, sans-serif"
        font-weight="600"
    >
        @{safe_username}
    </text>

    <text
        x="665"
        y="82"
        text-anchor="end"
        fill="#8b949e"
        font-size="13"
        font-family="Arial, sans-serif"
    >
        Updated: {safe_fetched_at}
    </text>

    <line
        x1="35"
        y1="105"
        x2="665"
        y2="105"
        stroke="#30363d"
        stroke-width="1"
    />
"""

    # Language rows
    y = header_height

    label_x = 35
    bar_x = 190
    bar_width = 350
    percent_x = 665

    for language, percent in languages:
        safe_language = escape(language)
        display_language = shorten(safe_language)

        color = LANGUAGE_COLORS.get(language, "#8b949e")

        # Minimum visible width for tiny percentages.
        filled_width = max(3, (float(percent) / 100) * bar_width)

        svg += f"""
    <!-- {safe_language} -->
    <circle
        cx="{label_x + 7}"
        cy="{y + 3}"
        r="7"
        fill="{color}"
    />

    <text
        x="{label_x + 25}"
        y="{y + 8}"
        fill="#e6edf3"
        font-size="15"
        font-family="Arial, sans-serif"
        font-weight="600"
    >
        {display_language}
    </text>

    <!-- Background bar -->
    <rect
        x="{bar_x}"
        y="{y - 8}"
        width="{bar_width}"
        height="14"
        rx="7"
        fill="#161b22"
    />

    <!-- Filled bar -->
    <rect
        x="{bar_x}"
        y="{y - 8}"
        width="{filled_width}"
        height="14"
        rx="7"
        fill="{color}"
    />

    <text
        x="{percent_x}"
        y="{y + 7}"
        text-anchor="end"
        fill="{color}"
        font-size="14"
        font-family="Arial, sans-serif"
        font-weight="700"
    >
        {float(percent):.2f}%
    </text>
"""

        y += row_height

    # Stats summary panel
    stats_y = y + 5

    svg += f"""
    <!-- Summary panel -->
    <rect
        x="35"
        y="{stats_y}"
        width="630"
        height="80"
        rx="12"
        fill="#161b22"
        stroke="#30363d"
        stroke-width="1"
    />

    <!-- Repository count -->
    <text
        x="65"
        y="{stats_y + 32}"
        fill="#f0f6fc"
        font-size="21"
        font-family="Arial, sans-serif"
        font-weight="700"
    >
        {repo_count if repo_count is not None else "—"}
    </text>

    <text
        x="65"
        y="{stats_y + 55}"
        fill="#8b949e"
        font-size="13"
        font-family="Arial, sans-serif"
    >
        Repositories
    </text>

    <!-- Divider -->
    <line
        x1="250"
        y1="{stats_y + 18}"
        x2="250"
        y2="{stats_y + 62}"
        stroke="#30363d"
    />

    <!-- Total bytes -->
    <text
        x="285"
        y="{stats_y + 32}"
        fill="#f0f6fc"
        font-size="21"
        font-family="Arial, sans-serif"
        font-weight="700"
    >
        {format_bytes(total_bytes)}
    </text>

    <text
        x="285"
        y="{stats_y + 55}"
        fill="#8b949e"
        font-size="13"
        font-family="Arial, sans-serif"
    >
        Total Bytes
    </text>

    <!-- Divider -->
    <line
        x1="470"
        y1="{stats_y + 18}"
        x2="470"
        y2="{stats_y + 62}"
        stroke="#30363d"
    />

    <!-- Language count -->
    <text
        x="505"
        y="{stats_y + 32}"
        fill="#f0f6fc"
        font-size="21"
        font-family="Arial, sans-serif"
        font-weight="700"
    >
        {len(percentages)}
    </text>

    <text
        x="505"
        y="{stats_y + 55}"
        fill="#8b949e"
        font-size="13"
        font-family="Arial, sans-serif"
    >
        Languages
    </text>

    <!-- Footer -->
    <text
        x="350"
        y="{stats_y + 110}"
        text-anchor="middle"
        fill="#8b949e"
        font-size="13"
        font-family="Arial, sans-serif"
    >
        ✦ Generated by
        <tspan fill="#58a6ff" font-weight="700">
            GitHubStats
        </tspan>
    </text>

</svg>
"""

    return svg
