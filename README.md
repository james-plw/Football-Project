# Football-Project
Planning to scrape live football match data to produce graphs detailing the story of a game

## Scraping Logic
When scraping stats from the BBC match page:
* The basic stats are always inside: <section aria-labelledby="basic-match-stats">
* Each normal stat row appears within: <div class="ssrcss-1onbazr-Section">
* The pie-chart stats (possession, touches in box) are stored inside: <span class="visually-hidden">
* The advanced stats are grouped in sections like: <section aria-labelledby="advanced-match-stats-attack|expected|distribution|defence">
* And each stat row inside these groups is wrapped in: <div class="ssrcss-17m9s2s-StatWrapper">
* Note: ssrcss-* class names are auto-generated and might change, so future BBC CSS changes can break this logic. I need to improve the code to be future-proof 

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