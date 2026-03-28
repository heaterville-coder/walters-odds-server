import requests
from flask import Flask, jsonify
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
    try:
        r = requests.get(
            'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries',
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
