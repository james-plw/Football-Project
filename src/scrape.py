''''''
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json

BBC_URL = 'https://www.bbc.co.uk/sport/football/live/czxyqddyj8wt#MatchStats'


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
    """Parse the HTML and extract match stats into a structured list."""
    soup = BeautifulSoup(html, "html.parser")

    stats = {"basic": [], "advanced": {}}

    # Basic stats
    basic_section = soup.select_one(
        "section[aria-labelledby='basic-match-stats']")
    if basic_section:
        # Normal stats
        for row in basic_section.select("div.ssrcss-1onbazr-Section"):
            parts = row.get_text(" ", strip=True).split(" ")
            i = find_first_numerical_value(parts)
            print(parts)
            stats["basic"].append({
                "stat": " ".join(parts[:i-1]),
                "home_team": parts[i-1],
                "home_val": parts[i],
                "away_team": parts[i+1],
                "away_val": parts[i+2]
            })
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

    # Advanced stats - currently empty!
    adv_wrapper = soup.select_one(
        "div.ssrcss-13rarkc-AdvancedMatchStatsWrapper")
    if adv_wrapper:
        for section in adv_wrapper.select("section"):
            label = section.get("aria-labelledby", "unknown")
            adv_rows = section.select("div.ssrcss-1onbazr-Section")
            advanced_stats = []
            for row in adv_rows:
                parts = row.get_text(" ", strip=True).split(" ")
                print(parts)
                advanced_stats.append({
                    "stat": parts[0],
                    "home_team": parts[1],
                    "home_val": parts[2],
                    "away_team": parts[3],
                    "away_val": parts[4]
                })
            stats["advanced"][label] = advanced_stats

    return stats


def find_first_numerical_value(parts: list) -> int:
    for i in range(0, len(parts)):
        try:
            float(parts[i])
            first_number_index = i
            break
        except ValueError:
            continue
    return first_number_index


def extract_hidden_stat(wrapper, label=None):
    """Extract a stat from a wrapper that uses visually-hidden spans."""
    spans = wrapper.select("span.visually-hidden")
    if not spans:
        return None

    home_team, home_val = spans[0].get_text(strip=True).split(" ", 1)
    away_team, away_val = spans[1].get_text(strip=True).split(" ", 1)

    return {
        "stat": label,
        "home_team": home_team,
        "home_val": home_val,
        "away_team": away_team,
        "away_val": away_val
    }


if __name__ == "__main__":
    html = fetch_match_html(BBC_URL)
    snapshot = parse_match_stats(html)
    print(json.dumps(snapshot, indent=2))

    # match_html = get_html(BBC_URL)
    # print(match_html)
    # scraped_games = parse_games_bs(steam_html)
