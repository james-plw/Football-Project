# Football-Project
Planning to scrape live football match data to produce graphs detailing the story of a game

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