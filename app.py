import os
import requests
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

ODDS_KEY = '1c8ca515de9faccc4419c2152a38d0c3'
RAPID_KEY = '76a5a3fd10msh865bce1bb1548d5p12ddd5jsn048a04eedfa2'
ODDS_BASE = 'https://api.the-odds-api.com/v4'
RAPID_BASE = 'https://tank01-fantasy-stats.p.rapidapi.com'
RAPID_HEADERS = {
    'x-rapidapi-key': RAPID_KEY,
    'x-rapidapi-host': 'tank01-fantasy-stats.p.rapidapi.com'
}

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
    r = requests.get(
        RAPID_BASE + '/getNBAInjuryList',
        headers=RAPID_HEADERS
    )
    data = r.json()
    injured = []
    for player in data.get('body', []):
        status = player.get('injStatus', '').strip()
        if status and status.lower() not in ['active', '']:
            injured.append({
                'name': player.get('longName', ''),
                'team': player.get('team', ''),
                'status': status,
                'injury': player.get('injDesc', ''),
                'returnDate': player.get('injReturnDate', 'TBD')
            })
    injured.sort(key=lambda x: x['team'])
    return jsonify(injured)

@app.route('/mlb-injuries')
def mlb_injuries():
    r = requests.get(
        RAPID_BASE + '/getMLBInjuryList',
        headers=RAPID_HEADERS
    )
    data = r.json()
    injured = []
    for player in data.get('body', []):
        status = player.get('injStatus', '').strip()
        if status and status.lower() not in ['active', '']:
            injured.append({
                'name': player.get('longName', ''),
                'team': player.get('team', ''),
                'status': status,
                'injury': player.get('injDesc', ''),
                'returnDate': player.get('injReturnDate', 'TBD')
            })
    injured.sort(key=lambda x: x['team'])
    return jsonify(injured)

if __name__ == '__main__':
    app.run()
