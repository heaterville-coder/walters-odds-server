import requests
from datetime import datetime, timedelta
from flask import Flask, jsonify, redirect
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

ODDS_KEY = '1c8ca515de9faccc4419c2152a38d0c3'
ODDS_BASE = 'https://api.the-odds-api.com/v4'

@app.route('/mlb')
def mlb():
    r = requests.get(
        ODDS_BASE + '/sports/baseball_mlb/odds',
        params={
            'apiKey': ODDS_KEY,
            'regions': 'us',
            'markets': 'h2h,spreads,totals',
            'oddsFormat': 'american',
            'bookmakers': 'draftkings,fanduel'
        }
    )
    return jsonify(r.json())

@app.route('/nba')
def nba():
    r = requests.get(
        ODDS_BASE + '/sports/basketball_nba/odds',
        params={
            'apiKey': ODDS_KEY,
            'regions': 'us',
            'markets': 'h2h,spreads,totals',
            'oddsFormat': 'american',
            'bookmakers': 'draftkings,fanduel'
        }
    )
    return jsonify(r.json())

@app.route('/nhl')
def nhl():
    r = requests.get(
        ODDS_BASE + '/sports/icehockey_nhl/odds',
        params={
            'apiKey': ODDS_KEY,
            'regions': 'us',
            'markets': 'h2h,spreads,totals',
            'oddsFormat': 'american',
            'bookmakers': 'draftkings,fanduel'
        }
    )
    return jsonify(r.json())

@app.route('/nba-injuries')
def nba_injuries():
    now = datetime.utcnow()
    times_to_try = [
        '07_15PM', '06_30PM', '05_30PM', '04_30PM',
        '03_30PM', '02_00PM', '11_00AM', '09_30AM', '05_00AM'
    ]
    for days_back in range(2):
        date_str = (now - timedelta(days=days_back)).strftime('%Y-%m-%d')
        for time_str in times_to_try:
            url = 'https://ak-static.cms.nba.com/referee/injury/Injury-Report_' + date_str + '_' + time_str + '.pdf'
            try:
                r = requests.get(url, timeout=6)
                if r.status_code == 200:
                    return jsonify({'pdf_url': url, 'date': date_str, 'time': time_str})
            except Exception:
                continue
    return jsonify({'error': 'No injury report found'})

@app.route('/mlb-injuries')
def mlb_injuries():
    try:
        r = requests.get(
            'https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/injuries',
            timeout=10
        )
        data = r.json()
        injured = []
        for team in data.get('injuries', []):
            team_name = team.get('team', {}).get('abbreviation', '')
            for player in team.get('injuries', []):
                injured.append({
                    'name': player.get('athlete', {}).get('displayName', ''),
                    'team': team_name,
                    'status': player.get('status', ''),
                    'injury': player.get('shortComment', ''),
                    'detail': player.get('longComment', '')
                })
        injured.sort(key=lambda x: x['team'])
        return jsonify(injured)
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run()
