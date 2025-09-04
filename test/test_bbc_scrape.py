# pylint: skip-file
import pytest
import datetime
from bs4 import BeautifulSoup

from src.bbc_scrape import (parse_match_stats, extract_team_names,
                            find_first_float, get_stats_from_arr,
                            extract_hidden_stat, fetch_kickoff_time)


def test_parse_match_stats():
    html = """
    <html>
      <body>
        <section aria-labelledby="basic-match-stats">
          <div>Shots TeamA 10 TeamB 12</div>
          <div>
            <span class="visually-hidden">TeamA 55%</span>
            <span class="visually-hidden">TeamB 45%</span>
          </div>
        </section>
        <section aria-labelledby="advanced-match-stats-1">
          <div>Fouls TeamA 3 TeamB 5</div>
        </section>
      </body>
    </html>
    """
    stats = parse_match_stats(html)
    assert "basic" in stats
    assert any(s["stat"] == "Shots" for s in stats["basic"])
    assert any(s["stat"] == "Possession" for s in stats["basic"])
    assert "advanced-match-stats-1" in stats["advanced"]
    assert stats["advanced"]["advanced-match-stats-1"][0]["stat"] == "Fouls"


def test_extract_team_names_works():
    html = """
    <section aria-labelledby="basic-match-stats">
      <div>Shots TeamA 10 Team B 12</div>
    </section>
    """
    soup = BeautifulSoup(html, "html.parser")
    section = soup.select_one("section[aria-labelledby='basic-match-stats']")
    result = extract_team_names(section)
    assert result["Home Team"] == "TeamA"
    assert result["Away Team"] == "Team B"
    assert result["Home Length"] == 1
    assert result["Away Length"] == 2


def test_extract_team_names_raises_error():
    html = """<section aria-labelledby="basic-match-stats"><div>Fouls 5 7</div></section>"""
    soup = BeautifulSoup(html, "html.parser")
    with pytest.raises(RuntimeError):
        extract_team_names(soup)


def test_find_first_float():
    arr = ["Shots", "TeamA", "10", "TeamB", "12"]
    assert find_first_float(arr) == 2


def test_find_first_float_second_number():
    arr = ["X", "1.5", "Y", "Z", "3.2"]
    assert find_first_float(arr, start=2) == 4


def test_find_first_float_error_if_no_number():
    with pytest.raises(ValueError):
        find_first_float(["a", "b", "c"])


def test_get_stats_from_arr():
    arr = ["Shots", "TeamA", "10", "TeamB", "12"]
    teams = {"Home Team": "TeamA", "Away Team": "TeamB",
             "Home Length": 1, "Away Length": 1}
    result = get_stats_from_arr(arr, teams)
    assert result == {
        "stat": "Shots",
        "home_team": "TeamA",
        "home_val": "10",
        "away_team": "TeamB",
        "away_val": "12"
    }


def test_extract_hidden_stat_parses_hidden_spans():
    html = """
    <div>
        <span class="visually-hidden">HomeTeam 55%</span>
        <span class="visually-hidden">AwayTeam 45%</span>
    </div>
    """
    soup = BeautifulSoup(html, "html.parser")
    result = extract_hidden_stat(soup, label="Possession")
    assert result == {
        "stat": "Possession",
        "home_team": "HomeTeam",
        "home_val": "55%",
        "away_team": "AwayTeam",
        "away_val": "45%"
    }


def test_extract_hidden_stat_returns_none_if_no_spans():
    html = "<div>No spans here</div>"
    soup = BeautifulSoup(html, "html.parser")
    assert extract_hidden_stat(soup) is None


def test_fetch_kickoff_time_valid_datetime():
    html = """
    <html>
      <body>
        <time>Sat 14 Sep 2025</time>
        <time>15:00</time>
      </body>
    </html>
    """
    dt = fetch_kickoff_time(html)
    assert isinstance(dt, datetime.datetime)
    assert dt.year == 2025
    assert dt.hour == 15
    assert dt.minute == 0


def test_fetch_kickoff_time_missing_date():
    html = "<html><body><time>15:00</time></body></html>"
    assert fetch_kickoff_time(html) is None


def test_fetch_kickoff_time_missing_time():
    html = "<html><body><time>Sat 14 Sep 2025</time></body></html>"
    assert fetch_kickoff_time(html) is None
