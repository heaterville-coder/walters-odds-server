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

def parse_pdf_bytes(pdf_bytes):
    try:
        import io
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(pdf_bytes))
        full_text = ''
        for page in reader.pages:
            full_text += page.extract_text() + '\n'
        return full_text
    except Exception as e:
        return ''

def parse_injury_text(text):
    players = []
    statuses = ['Out', 'Questionable', 'Doubtful', 'Probable']
    skip_words = ['Game Date', 'Game Time', 'Matchup', 'Player Name', 'Current Status', 'Reason', 'Page', 'Injury Report']
    lines = text.split('\n')
    current_team = ''

    team_patterns = [
        'Atlanta Hawks', 'Boston Celtics', 'Brooklyn Nets', 'Charlotte Hornets',
        'Chicago Bulls', 'Cleveland Cavaliers', 'Dallas Mavericks', 'Denver Nuggets',
        'Detroit Pistons', 'Golden State Warriors', 'Houston Rockets', 'Indiana Pacers',
        'LA Clippers', 'Los Angeles Lakers', 'Memphis Grizzlies', 'Miami Heat',
        'Milwaukee Bucks', 'Minnesota Timberwolves', 'New Orleans Pelicans', 'New York Knicks',
        'Oklahoma City Thunder', 'Orlando Magic', 'Philadelphia 76ers', 'Phoenix Suns',
        'Portland Trail Blazers', 'Sacramento Kings', 'San Antonio Spurs', 'Toronto Raptors',
        'Utah Jazz', 'Washington Wizards'
    ]

    team_abbr = {
        'Atlanta Hawks': 'ATL', 'Boston Celtics': 'BOS', 'Brooklyn Nets': 'BKN',
        'Charlotte Hornets': 'CHA', 'Chicago Bulls': 'CHI', 'Cleveland Cavaliers': 'CLE',
        'Dallas Mavericks': 'DAL', 'Denver Nuggets': 'DEN', 'Detroit Pistons': 'DET',
        'Golden State Warriors': 'GSW', 'Houston Rockets': 'HOU', 'Indiana Pacers': 'IND',
        'LA Clippers': 'LAC', 'Los Angeles Lakers': 'LAL', 'Memphis Grizzlies': 'MEM',
        'Miami Heat': 'MIA', 'Milwaukee Bucks': 'MIL', 'Minnesota Timberwolves': 'MIN',
        'New Orleans Pelicans': 'NOP', 'New York Knicks': 'NYK', 'Oklahoma City Thunder': 'OKC',
        'Orlando Magic': 'ORL', 'Philadelphia 76ers': 'PHI', 'Phoenix Suns': 'PHX',
        'Portland Trail Blazers': 'POR', 'Sacramento Kings': 'SAC', 'San Antonio Spurs': 'SAS',
        'Toronto Raptors': 'TOR', 'Utah Jazz': 'UTA', 'Washington Wizards': 'WAS'
    }

    for line in lines:
        line = line.strip()
        if not line:
            continue

        skip = False
        for sw in skip_words:
            if line.startswith(sw):
                skip = True
                break
        if skip:
            continue

        for team in team_patterns:
            if team in line:
                current_team = team_abbr.get(team, team)
                break

        found_status = None
        for s in statuses:
            if s in line:
                found_status = s
                break

        if found_status:
            parts = line.split(found_status)
            name_part = parts[0].strip()
            reason_part = parts[1].strip() if len(parts) > 1 else ''

            if name_part and len(name_part) > 2 and not any(c.isdigit() for c in name_part[:3]):
                if 'NOT YET SUBMITTED' not in name_part and 'G League' not in reason_part[:10]:
                    players.append({
                        'name': name_part,
                        'team': current_team,
                        'status': found_status,
                        'injury': reason_part[:120]
                    })

    return players

@app.route('/nba-injuries')
def nba_injuries():
    now = datetime.utcnow()
    date_str = now.strftime('%Y-%m-%d')
    times_to_try = [
        '07_15PM', '06_30PM', '05_30PM', '04_30PM',
        '03_30PM', '02_00PM', '11_00AM', '09_30AM', '05_00AM'
    ]

    for time_str in times_to_try:
        pdf_bytes, url = try_nba_pdf(date_str, time_str)
        if pdf_bytes:
            text = parse_pdf_bytes(pdf_bytes)
            if text:
                players = parse_injury_text(text)
                if players:
                    return jsonify(players)

    yesterday = (now - timedelta(days=1)).strftime('%Y-%m-%d')
    for time_str in ['07_15PM', '06_30PM', '05_30PM']:
        pdf_bytes, url = try_nba_pdf(yesterday, time_str)
        if pdf_bytes:
            text = parse_pdf_bytes(pdf_bytes)
            if text:
                players = parse_injury_text(text)
                if players:
                    return jsonify(players)

    return jsonify({'error': 'Could not parse injury report'})

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
