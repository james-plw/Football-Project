'''Module for scraping match stats data from the BBC page for a football game'''
import json  # for data output
from playwright.sync_api import sync_playwright  # for launching browser instances
from bs4 import BeautifulSoup  # for parsing HTML

BBC_URL = 'https://www.bbc.co.uk/sport/football/live/czxyqddyj8wt#MatchStats'
BBC_URL_2 = 'https://www.bbc.co.uk/sport/football/live/c04r3pnn32vt#MatchStats'

# hard coded to make it easier to account for different-length football club names
BBC_STAT_NAMES = ['xG', 'Shots', 'Shots on target', 'Total touches inside the opposition box',
                  'Goalkeeper saves', 'Fouls committed', 'Corners', 'Shots off target',
                  'Attempts out of box', 'Total offsides', 'xG from open play',
                  'xG from set play', 'xA', 'Total passes', 'Pass accuracy %',
                  'Backward passes', 'Forward passes', 'Total long balls',
                  'Successful final third passes', 'Total crosses', 'Total tackles',
                  'Won tackle %', 'Fouls committed', 'Total yellow cards', 'Total clearances',
                  'Clearances off the line']
# sorted by longest stat-names first, to avoid Shots on target matching with Shots incorrectly
SORTED_STAT_NAMES = sorted(BBC_STAT_NAMES, key=lambda s: -len(s.split()))


def fetch_match_html(url: str) -> str:
    """Fetch the fully rendered HTML for the BBC match stats page."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        # Wait until the Match Stats tab has loaded
        page.wait_for_selector("section[aria-labelledby='basic-match-stats']")
        html = page.content()
        browser.close()
    return html


def parse_match_stats(html: str) -> list[dict]:
    """Parse the HTML and extract match stats into a structured dict."""
    soup = BeautifulSoup(html, "html.parser")

    stats = {"basic": [], "advanced": {}}

    # Basic stats
    basic_section = soup.select_one(
        "section[aria-labelledby='basic-match-stats']")
    if basic_section:
        # Normal stats
        for row in basic_section.select("div.ssrcss-1onbazr-Section"):
            parts = row.get_text(" ", strip=True).split(" ")
            if len(parts) >= 5:
                stats["basic"].append(get_stats_from_arr(parts))
        # Possession
        for wrapper in basic_section.select("div.ssrcss-1a050bw-Wrapper"):
            stat = extract_hidden_stat(wrapper, label="Possession")
            if stat:
                stats["basic"].append(stat)
        # Touches in opposition box
        for wrapper in basic_section.select("div.ssrcss-3tqs06-Wrapper"):
            stat = extract_hidden_stat(
                wrapper, label="Total touches inside the opposition box")
            if stat:
                stats["basic"].append(stat)

    # Advanced stats
    adv_sections = soup.find_all("section", {
        "aria-labelledby": lambda v: v and v.startswith("advanced-match-stats")
    })

    for section in adv_sections:
        label = section["aria-labelledby"]
        adv_rows = section.select("div.ssrcss-17m9s2s-StatWrapper")
        advanced_stats = []
        for row in adv_rows:
            parts = row.get_text(" ", strip=True).split(" ")
            if len(parts) >= 5:
                advanced_stats.append(get_stats_from_arr(parts))
        stats["advanced"][label] = advanced_stats
    return stats


def get_stats_from_arr(arr: list) -> dict:
    matched_stat = next(
        (stat for stat in SORTED_STAT_NAMES if arr[:len(
            stat.split())] == stat.split()),
        None)
    first_val = find_first_float(arr)
    second_val = find_first_float(arr, start=first_val + 1)
    return {
        "stat": matched_stat,
        "home_team": ' '.join(arr[len(matched_stat.split()):first_val]),
        "home_val": arr[first_val],
        "away_team": ' '.join(arr[first_val+1:second_val]),
        "away_val": arr[second_val]
    }


def find_first_float(arr: list, start=0) -> int:
    '''Finds the first numerical value in a list'''
    for i, val in enumerate(arr[start:], start=start):
        try:
            float(val)
            return i
        except ValueError:
            continue
    raise ValueError("No numeric value found in list")


def extract_hidden_stat(wrapper, label=None):
    """Extract a stat from a wrapper that uses visually-hidden spans."""
    spans = wrapper.select("span.visually-hidden")
    if not spans:
        return None

    home_team, home_val = spans[0].get_text(strip=True).rsplit(" ", 1)
    away_team, away_val = spans[1].get_text(strip=True).rsplit(" ", 1)

    return {
        "stat": label,
        "home_team": home_team,
        "home_val": home_val,
        "away_team": away_team,
        "away_val": away_val
    }


if __name__ == "__main__":
    bbc_html = fetch_match_html(BBC_URL)
    match_stats = parse_match_stats(bbc_html)
    print(json.dumps(match_stats, indent=2))
