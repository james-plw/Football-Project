# Football-Project
Planning to scrape live football match data to produce graphs detailing the story of a game

## Scraping Logic
When scraping stats from the BBC match page:
* The basic stats are always inside: <section aria-labelledby="basic-match-stats">
* Each stat row is a direct <div> child of this section.
* Team names are extracted from the "Shots" stat row (since it is the most reliable stat to be tracked by BBC).
* Normal stats (e.g. Corners) are parsed by splitting text and detecting the 1st and 2nd numeric values, along with using the number of words in each team name.
* Possession is handled as a special case — it appears as two <span class="visually-hidden"> elements containing percentages (e.g. Chelsea 53.8%).
* The advanced stats are grouped in sections like: <section aria-labelledby="advanced-match-stats-attack"> with `attack` being the group name.
* Each stat row is a direct <div> child inside these sections.
* Stats are parsed using the same logic as for basic stats.
* The section’s `aria-labelledby` value is used as the group name in the output.

## File structures
- .github
    - Utility folder used for github configs
- src
    - bbc_scrape.py
        - Module takes URL of a BBC match page and scrapes the match stats
- test
    - Contains testing scripts for each module

## How to run
1. Install Python 3 on your system
2. Run `python3 -m venv .venv` to make a new virtual environment
3. Run `activate .venv/bin/activate` to enter the venv
4. Run `pip install -r requirements.txt` at the top level of the project
5. To test: `python3 -m pytest test/*.py`