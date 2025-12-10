
def generate_stats_svg(username: str, percentages: dict):
    # Card size
    width = 500
    height = 200 + (len(percentages) * 30)

    # Background
    svg = f"""
    <svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
        <rect width="100%" height="100%" fill="#1e1e1e" rx="10" />
        
        <text x="20" y="40" fill="white" font-size="24" font-weight="bold">
            GitHub Stats • {username}
        </text>
    """

    y = 80
    bar_width = 350

    for lang, percent in percentages.items():
        svg += f"""
        <text x="20" y="{y}" fill="#cccccc" font-size="16">{lang}</text>

        <rect x="150" y="{y - 12}" width="{percent * 3.5}" height="10" fill="#4caf50" rx="3" />

        <text x="{150 + percent * 3.5 + 10}" y="{y - 3}" fill="#ffffff" font-size="14">
            {percent}%
        </text>
        """
        y += 30

    svg += "</svg>"
    return svg
