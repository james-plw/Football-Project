# Football-Project
Planning to scrape live football match data to produce graphs detailing the story of a game

## Scraping Logic
When grabbing stats from the BBC web page for a game:
* The basic stats are always inside: section[aria-labelledby="basic-match-stats"].
* Each normal stat row uses the same: <div class="ssrcss-1onbazr-Section">
* The pie-charts (possession, touches in box) always use: span.visually-hidden
* The advanced stats are grouped: <section aria-labelledby="advanced-match-stats-attack|expected|distribution|defence">
* With the stats within each group in: div.ssrcss-17m9s2s-StatWrapper

## File structures
- .github
    - Utility folder used for github configs
- src
- test
    - Contains testing scripts for each module

## How to run
1. Install Python 3 on your system
2. Run `python3 -m venv .venv` to make a new virtual environment
3. Run `activate .venv/bin/activate` to enter the venv
4. Run `pip install -r requirements.txt` at the top level of the project
5. To test: `python3 -m pytest test/*.py`