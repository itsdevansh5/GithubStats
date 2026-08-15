from xml.sax.saxutils import escape

def shorten(text, max_chars=12):
    if len(text) > max_chars:
        return text[:max_chars - 3] + "..."
    return text
def generate_stats_svg(username: str, percentages: dict):
    # Card size
    width = 500
    height = 200 + (len(percentages) * 30)
    safe_username= escape(username)
    # Background
    svg = f"""
    <svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
        <rect width="100%" height="100%" fill="#0d1117" rx="10" />
        
        <text x="20" y="40" fill="#e6edf3" font-size="24" font-weight="bold">
            GitHub Stats • {safe_username}
        </text>
    """

    y = 80
    bar_width = 350

    for lang, percent in percentages.items():
        safe_lang = escape(lang)
        svg += f"""
        <text x="20" y="{y}" fill="#8b949e" font-size="16">{shorten(safe_lang)}</text>

        <rect x="150" y="{y - 12}" width="{percent * 3.5}" height="10" fill="#58a6ff" rx="3" />

        <text x="{150 + percent * 3.5 + 10}" y="{y - 3}" fill="#ffffff" font-size="14">
            {percent}%
        </text>
        """
        y += 30

    svg += "</svg>"
    return svg
