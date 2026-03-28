import re
import requests
from datetime import datetime, timedelta
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

def try_nba_pdf(date_str, time_str):
    url = 'https://ak-static.cms.nba.com/referee/injury/Injury-Report_' + date_str + '_' + time_str + '.pdf'
    try:
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            return r.content, url
    except Exception:
        pass
    return None, None

def parse_nba_pdf(pdf_bytes):
    try:
        import pdfplumber
        import io
        players = []
        statuses = ['Out', 'Questionable', 'Doubtful', 'Probable', 'Available']
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue
                lines = text.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    found_status = None
                    for s in statuses:
                        if s in line:
                            found_status = s
                            break
                    if found_status and found_status != 'Available':
                        parts = line.split(found_status)
                        name_part = parts[0].strip()
                        reason_part = parts[1].strip() if len(parts) > 1 else ''
                        if name_part and len(name_part) > 2:
                            players.append({
                                'name': name_part,
                                'team': '',
                                'status': found_status,
                                'injury': reason_part
                            })
        return players
    except Exception as e:
        return []

@app.route('/nba-injuries')
def nba_injuries():
    now = datetime.utcnow()
    date_str = now.strftime('%Y-%m-%d')
    times_to_try = ['07_15PM', '06_30PM', '05_30PM', '04_30PM', '03_30PM', '02_00PM', '11_00AM', '09_30AM', '05_00AM']
    for time_str in times_to_try:
        pdf_bytes, url = try_nba_pdf(date_str, time_str)
        if pdf_bytes:
            players = parse_nba_pdf(pdf_bytes)
            if players:
                return jsonify(players)
            return jsonify({'source': url, 'note': 'PDF found - install pdfplumber to parse', 'url': url})
    yesterday = (now - timedelta(days=1)).strftime('%Y-%m-%d')
    for time_str in ['07_15PM', '06_30PM', '05_30PM']:
        pdf_bytes, url = try_nba_pdf(yesterday, time_str)
        if pdf_bytes:
            players = parse_nba_pdf(pdf_bytes)
            if players:
                return jsonify(players)
            return jsonify({'source': url, 'note': 'PDF found - install pdfplumber to parse', 'url': url})
    return jsonify({'error': 'No injury report PDF found'})

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

