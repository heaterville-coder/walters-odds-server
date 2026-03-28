from flask import Flask, jsonify
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

API_KEY = '1c8ca515de9faccc4419c2152a38d0c3'
BASE = 'https://api.the-odds-api.com/v4'

@app.route('/mlb')
def mlb():
    r = requests.get(
        BASE + '/sports/baseball_mlb/odds',
        params={
            'apiKey': API_KEY,
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
        BASE + '/sports/basketball_nba/odds',
        params={
            'apiKey': API_KEY,
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
        BASE + '/sports/icehockey_nhl/odds',
        params={
            'apiKey': API_KEY,
            'regions': 'us',
            'markets': 'h2h,spreads,totals',
            'oddsFormat': 'american',
            'bookmakers': 'draftkings,fanduel'
        }
    )
    return jsonify(r.json())

if __name__ == '__main__':
    app.run()
