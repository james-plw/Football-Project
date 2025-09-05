'''Module for scraping match stats data from the BBC page for a football game'''
import argparse
import datetime
import time
# import json  # for data output
from playwright.sync_api import sync_playwright  # for launching browser instances
from bs4 import BeautifulSoup  # for parsing HTML
from bs4.element import Tag  # type hints
import pandas as pd

FUTURE_URL = 'https://www.bbc.co.uk/sport/football/live/c626pmgznp6t'


def handle_cl_args() -> str:
    '''Handles command line arguments for chosen match URL'''
    parser = argparse.ArgumentParser()
    parser.add_argument('url', help='BBC match URL')
    args = parser.parse_args()
    url = args.url
    if not url.startswith('https://www.bbc.co.uk/sport/football'):
        raise ValueError('Invalid URL')
    return url


def fetch_match_html(url: str) -> str:
    """Fetch the fully rendered HTML for the BBC match stats page."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        if 'MatchStats' in url:
            # Wait until the Match Stats tab has loaded
            page.wait_for_selector(
                "section[aria-labelledby='basic-match-stats']")
        else:
            page.wait_for_selector("body")
        html = page.content()
        browser.close()
    return html


def fetch_kickoff_time(html: str) -> datetime:
    '''Fetch the kickoff date and time for future matches - to use for scheduling'''
    soup = BeautifulSoup(html, "html.parser")

    # Get the date from a <time> tag containing 3 or more words
    date_tag = soup.find("time", string=lambda s: s and len(s.split()) >= 3)
    if not date_tag:
        return None
    date_str = date_tag.get_text(strip=True)

    # Get the kickoff from a <time> tag containing ':'
    time_tag = soup.find("time", string=lambda s: s and ":" in s)
    if not time_tag:
        return None
    time_str = time_tag.get_text(strip=True)

    # Combine into a datetime
    try:
        dt = datetime.datetime.strptime(
            f"{date_str} {time_str}", "%a %d %b %Y %H:%M")
        return dt
    except ValueError:
        return None


def sleep_until_kickoff(kickoff: datetime):
    '''Calculates time until kickoff and sleeps until then'''
    now = datetime.datetime.now()
    if kickoff > now:
        wait_seconds = (kickoff - now).total_seconds()
        print(f"Waiting {wait_seconds/60:.1f} minutes until kickoff...")
        time.sleep(wait_seconds)


def parse_match_stats(html: str) -> tuple[dict, dict]:
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
    return stats, teams


def extract_team_names(section: Tag) -> dict[str, str | int]:
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


def extract_hidden_stat(wrapper: Tag, label: str = None):
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


def create_filename(teams: dict, kickoff: datetime):
    '''Defines output filename from teams and date'''

    home_team = teams['Home Team'].replace(" ", "_")
    away_team = teams['Away Team'].replace(" ", "_")
    date_str = kickoff.strftime('%Y_%m_%d')

    return f"{home_team}_{away_team}_{date_str}.csv"


def build_row(stats: dict, teams: dict, timestamp: str, match_minute: int) -> dict:
    '''Builds a flat dict of stats for saving to a csv'''
    home_team = teams['Home Team'].replace(" ", "_")
    away_team = teams['Away Team'].replace(" ", "_")

    row = {"time": timestamp, "minute": match_minute}
    for stat in stats["basic"]:
        stat_name = stat["stat"].replace(" ", "_")
        row[f"{stat_name}_{home_team}"] = stat["home_val"]
        row[f"{stat_name}_{away_team}"] = stat["away_val"]

    for stat_list in stats["advanced"].values():
        for stat in stat_list:
            stat_name = stat["stat"].replace(" ", "_")
            row[f"{stat_name}_{home_team}"] = stat["home_val"]
            row[f"{stat_name}_{away_team}"] = stat["away_val"]

    return row


def scrape_every_minute(url: str, kickoff: datetime):
    '''Scrapes BBC match stats for chosen URL, waiting 60s between every attempt'''
    csv_file = None
    rows = []
    unchanged_count = 0
    try:
        while True:
            now = datetime.datetime.now()
            timestamp = now.strftime("%H:%M:%S")
            match_minute = int((now - kickoff).total_seconds() // 60)

            stats_html = fetch_match_html(url)
            match_stats, teams = parse_match_stats(stats_html)
            if not csv_file:
                csv_file = create_filename(teams, kickoff)

            # Creating flat dict to convert into a DataFrame
            row = build_row(match_stats, teams, timestamp, match_minute)

            # Check if stats changed since last scrape
            if rows and row == rows[-1]:
                unchanged_count += 1
                print(f"[{timestamp}] No change in stats.")
            else:
                unchanged_count = 0
                rows.append(row)
                print(f"[{timestamp}] Scraped stats (minute {match_minute}):")
                # print(json.dumps(match_stats, indent=2))

                # Append to CSV after each scrape
                df = pd.DataFrame(rows)
                df.to_csv(csv_file, index=False)
                print(f"Saving to {csv_file}")

            # Stop after if unchanged for 5 minutes after 90 mins + 15 mins break
            if match_minute >= 105 and unchanged_count >= 5:
                print("No changes detected after 90 minutes. Stopping scraper.")
                break
            time.sleep(60)
    except KeyboardInterrupt:
        print("Stopped scraping.")


if __name__ == "__main__":
    bbc_url = handle_cl_args()
    bbc_html = fetch_match_html(bbc_url)
    match_kickoff = fetch_kickoff_time(bbc_html)
    if not match_kickoff:
        raise RuntimeError("Could not find kickoff time for match")

    print(f"Kickoff scheduled at {match_kickoff}")

    sleep_until_kickoff(match_kickoff)

    match_stats_url = bbc_url + '#MatchStats'

    scrape_every_minute(match_stats_url, match_kickoff)
