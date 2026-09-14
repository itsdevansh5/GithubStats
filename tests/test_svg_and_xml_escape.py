import respx
from app.svg_generator import *

def test_svg_generation():
    
    percentages = {
        "Python": 60.0,
        "JavaScript": 40.0,
    }

    svg = generate_stats_svg("devansh", percentages)

    assert "<svg" in svg
    assert "GitHubStats" in svg
    assert "devansh" in svg
    assert "Python" in svg
    assert "JavaScript" in svg
    assert "60.00%" in svg
    assert "40.00%" in svg

def test_shorten():

    assert shorten("Python") == "Python"
    assert shorten("abcdefghijkl", 12) == "abcdefghijkl"
    assert shorten("abcdefghijklmnop", 12) == "abcdefghi..."

def test_generate_stats_svg_escapes_xml():

    percentages = {
        "<Python>": 100.0,
    }

    svg = generate_stats_svg(
        "<devansh>",
        percentages
    )

    assert "&lt;devansh&gt;" in svg
    assert "&lt;Python&gt;" in svg


def test_generate_stats_svg_full_percentage():

    percentages = {
        "Python": 100.0,
    }

    svg = generate_stats_svg("devansh", percentages)

    assert 'width="350.0"' in svg
