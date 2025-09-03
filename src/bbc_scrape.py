'''Module for scraping match stats data from the BBC page for a football game'''
import json  # for data output
from playwright.sync_api import sync_playwright  # for launching browser instances
from bs4 import BeautifulSoup  # for parsing HTML

BBC_URL = 'https://www.bbc.co.uk/sport/football/live/czxyqddyj8wt#MatchStats'
BBC_URL_2 = 'https://www.bbc.co.uk/sport/football/live/c04r3pnn32vt#MatchStats'


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
        teams = extract_team_names(basic_section)
        for row in basic_section.find_all("div", recursive=False):
            # Possession (two spans with percentages)
            spans = row.select("span.visually-hidden")
            if len(spans) == 2 and all("%" in s.get_text() for s in spans):
                stat = extract_hidden_stat(row, label="Possession")
                if stat:
                    stats["basic"].append(stat)
                continue
            # Normal stats
            parts = row.get_text(" ", strip=True).split(" ")
            try:
                stats['basic'].append(get_stats_from_arr(parts, teams))
            except ValueError:
                continue  # skip rows without numeric values

    # Advanced stats
    adv_sections = soup.find_all("section", {
        "aria-labelledby": lambda v: v and v.startswith("advanced-match-stats")
    })
    for section in adv_sections:
        label = section["aria-labelledby"]
        advanced_stats = []
        for row in section.find_all("div", recursive=False):
            parts = row.get_text(" ", strip=True).split(" ")
            try:
                advanced_stats.append(get_stats_from_arr(parts, teams))
            except ValueError:
                continue  # skip rows without numeric values
        stats["advanced"][label] = advanced_stats
    return stats


def extract_team_names(section) -> dict[str, str | int]:
    """Extract home/away team names from the 'Shots' stat row"""
    team_info = {}
    for row in section.find_all("div", recursive=False):
        parts = row.get_text(" ", strip=True).split(" ")
        if parts[0] == "Shots":
            # find positions of numeric values
            home_val = find_first_float(parts)
            away_val = find_first_float(parts, start=home_val + 1)
            team_info['Home Team'] = " ".join(
                parts[1:home_val])   # skip "Shots"
            team_info['Away Team'] = " ".join(parts[home_val+1:away_val])
            team_info['Home Length'] = len(team_info['Home Team'].split(' '))
            team_info['Away Length'] = len(team_info['Away Team'].split(' '))
            return team_info
    raise RuntimeError('No Shots stat found - unable to get team names')


def find_first_float(arr: list, start=0) -> int:
    '''Finds the first numerical value in a list'''
    for i, val in enumerate(arr[start:], start=start):
        try:
            float(val)
            return i
        except ValueError:
            continue
    raise ValueError("No numeric value found in list")


def get_stats_from_arr(arr: list, teams: dict) -> dict:
    '''Formats the stat from a list into a dict'''
    home_val = find_first_float(arr)
    away_val = find_first_float(arr, start=home_val + 1)
    return {
        "stat": ' '.join(arr[:home_val-teams['Home Length']]),
        "home_team": teams['Home Team'],
        "home_val": arr[home_val],
        "away_team": teams['Away Team'],
        "away_val": arr[away_val]
    }


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
