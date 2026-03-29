import requests
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

ODDS_KEY = '1c8ca515de9faccc4419c2152a38d0c3'
ODDS_BASE = 'https://api.the-odds-api.com/v4'

# ── BASELINE RATINGS (Simmons March 23 2026) ──────────────────────────────────

MLB_BASELINE = {
    'LAD': 5.91, 'TOR': 5.87, 'NYY': 5.61, 'PHI': 5.61, 'MIL': 5.58,
    'CHC': 5.51, 'BOS': 5.47, 'SEA': 5.37, 'SD':  5.31, 'DET': 5.25,
    'TEX': 5.17, 'HOU': 5.15, 'CLE': 5.12, 'NYM': 5.11, 'CIN': 5.04,
    'KC':  5.02, 'TB':  5.01, 'AZ':  4.99, 'SF':  4.98, 'ATL': 4.87,
    'STL': 4.78, 'ATH': 4.74, 'MIA': 4.73, 'BAL': 4.67, 'PIT': 4.65,
    'MIN': 4.54, 'LAA': 4.40, 'CWS': 4.31, 'WSH': 4.09, 'COL': 3.14
}

NBA_BASELINE = {
    'OKC': 57.20, 'SAS': 56.11, 'DET': 55.00, 'BOS': 54.22, 'NYK': 53.70,
    'DEN': 53.17, 'CLE': 53.14, 'HOU': 52.82, 'LAL': 52.62, 'MIN': 52.37,
    'PHX': 51.50, 'CHA': 51.48, 'MIA': 51.34, 'TOR': 51.31, 'ATL': 51.02,
    'ORL': 50.76, 'PHI': 50.46, 'LAC': 50.23, 'GSW': 50.08, 'POR': 49.87,
    'MIL': 47.04, 'CHI': 46.90, 'NOP': 46.88, 'MEM': 46.53, 'DAL': 45.78,
    'UTA': 44.78, 'BKN': 44.17, 'SAC': 43.75, 'IND': 43.09, 'WAS': 42.65
}

PARK_FACTORS = {
    'COL': 0.25, 'CIN': 0.25, 'BOS': 0.25, 'PHI': 0.25, 'TOR': 0.25,
    'NYY': 0.15, 'LAA': 0.15, 'MIL': 0.15, 'PIT': 0.15, 'KC':  0.15,
    'CHC': 0.15, 'BAL': 0.15,
    'ATL': 0.10, 'HOU': 0.10, 'STL': 0.10, 'TEX': 0.10, 'NYM': 0.10,
    'CLE': 0.10, 'MIN': 0.10, 'MIA': 0.10, 'WSH': 0.10, 'DET': 0.10,
    'TB':  0.10, 'CWS': 0.10,
    'SEA': 0.05, 'SD':  0.05, 'LAD': 0.05, 'SF':  0.05, 'ATH': 0.05,
    'AZ':  0.05
}

NBA_HOME = 3.0

mlb_ratings = dict(MLB_BASELINE)
nba_ratings = dict(NBA_BASELINE)
mlb_history = []
nba_history = []

# ── ODDS ──────────────────────────────────────────────────────────────────────

@app.route('/mlb')
def mlb():
    r = requests.get(ODDS_BASE + '/sports/baseball_mlb/odds', params={
        'apiKey': ODDS_KEY, 'regions': 'us',
        'markets': 'h2h,spreads,totals', 'oddsFormat': 'american',
        'bookmakers': 'draftkings,fanduel'
    })
    return jsonify(r.json())

@app.route('/nba')
def nba():
    r = requests.get(ODDS_BASE + '/sports/basketball_nba/odds', params={
        'apiKey': ODDS_KEY, 'regions': 'us',
        'markets': 'h2h,spreads,totals', 'oddsFormat': 'american',
        'bookmakers': 'draftkings,fanduel'
    })
    return jsonify(r.json())

@app.route('/nhl')
def nhl():
    r = requests.get(ODDS_BASE + '/sports/icehockey_nhl/odds', params={
        'apiKey': ODDS_KEY, 'regions': 'us',
        'markets': 'h2h,spreads,totals', 'oddsFormat': 'american',
        'bookmakers': 'draftkings,fanduel'
    })
    return jsonify(r.json())

# ── SCORES ────────────────────────────────────────────────────────────────────

@app.route('/mlb-scores')
def mlb_scores():
    r = requests.get(ODDS_BASE + '/sports/baseball_mlb/scores', params={
        'apiKey': ODDS_KEY, 'daysFrom': 1
    })
    return jsonify(r.json())

@app.route('/nba-scores')
def nba_scores():
    r = requests.get(ODDS_BASE + '/sports/basketball_nba/scores', params={
        'apiKey': ODDS_KEY, 'daysFrom': 1
    })
    return jsonify(r.json())

@app.route('/nhl-scores')
def nhl_scores():
    r = requests.get(ODDS_BASE + '/sports/icehockey_nhl/scores', params={
        'apiKey': ODDS_KEY, 'daysFrom': 1
    })
    return jsonify(r.json())

# ── INJURIES ──────────────────────────────────────────────────────────────────

def try_nba_pdf(date_str, time_str):
    url = 'https://ak-static.cms.nba.com/referee/injury/Injury-Report_' + date_str + '_' + time_str + '.pdf'
    try:
        r = requests.get(url, timeout=6)
        if r.status_code == 200:
            return r.content, url
    except Exception:
        pass
    return None, None

@app.route('/nba-injuries')
def nba_injuries():
    now = datetime.utcnow()
    times = ['07_15PM', '06_30PM', '05_30PM', '04_30PM', '03_30PM', '02_00PM', '11_00AM', '09_30AM', '05_00AM']
    for days_back in range(2):
        date_str = (now - timedelta(days=days_back)).strftime('%Y-%m-%d')
        for time_str in times:
            _, url = try_nba_pdf(date_str, time_str)
            if url:
                r = requests.get(url, timeout=6)
                if r.status_code == 200:
                    return jsonify({'pdf_url': url, 'date': date_str, 'time': time_str})
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

# ── RATINGS ───────────────────────────────────────────────────────────────────

@app.route('/ratings')
def ratings():
    mlb_sorted = sorted(mlb_ratings.items(), key=lambda x: x[1], reverse=True)
    nba_sorted = sorted(nba_ratings.items(), key=lambda x: x[1], reverse=True)
    return jsonify({
        'last_updated': datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC'),
        'mlb': {
            'ratings': dict(mlb_sorted),
            'baseline': 'Simmons 2026 Preseason',
            'games_processed': len(mlb_history)
        },
        'nba': {
            'ratings': dict(nba_sorted),
            'baseline': 'Simmons March 23 2026',
            'games_processed': len(nba_history)
        },
        'park_factors': PARK_FACTORS,
        'nba_home_court': NBA_HOME
    })

@app.route('/ratings/update', methods=['POST'])
def update_ratings():
    global mlb_ratings, nba_ratings, mlb_history, nba_history
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    sport    = data.get('sport', '').lower()
    away     = data.get('away_team', '').upper()
    home     = data.get('home_team', '').upper()
    away_sc  = data.get('away_score')
    home_sc  = data.get('home_score')
    away_inj = data.get('away_injury_adj', 0)
    home_inj = data.get('home_injury_adj', 0)
    date_str = data.get('date', datetime.utcnow().strftime('%Y-%m-%d'))

    if sport not in ['mlb', 'nba']:
        return jsonify({'error': 'sport must be mlb or nba'}), 400

    rat = mlb_ratings if sport == 'mlb' else nba_ratings

    if away not in rat or home not in rat:
        return jsonify({'error': 'Unknown team: ' + away + ' or ' + home}), 400

    away_r = rat[away]
    home_r = rat[home]
    hf = PARK_FACTORS.get(home, 0.10) if sport == 'mlb' else NBA_HOME

    tgpl_away = (away_sc - home_sc) + home_r - hf + away_inj
    tgpl_home = (home_sc - away_sc) + away_r + hf + home_inj

    new_away = round(0.9 * away_r + 0.1 * tgpl_away, 4)
    new_home = round(0.9 * home_r + 0.1 * tgpl_home, 4)

    rat[away] = new_away
    rat[home] = new_home

    record = {
        'date': date_str, 'away': away, 'home': home,
        'score': str(away_sc) + '-' + str(home_sc),
        'away_old': round(away_r, 4), 'away_new': new_away,
        'home_old': round(home_r, 4), 'home_new': new_home,
        'tgpl_away': round(tgpl_away, 4), 'tgpl_home': round(tgpl_home, 4)
    }

    if sport == 'mlb':
        mlb_history.append(record)
    else:
        nba_history.append(record)

    return jsonify({
        'status': 'updated',
        'game': away + ' @ ' + home,
        'score': str(away_sc) + '-' + str(home_sc),
        away: {'old': round(away_r, 4), 'tgpl': round(tgpl_away, 4), 'new': new_away},
        home: {'old': round(home_r, 4), 'tgpl': round(tgpl_home, 4), 'new': new_home}
    })

@app.route('/ratings/history')
def ratings_history():
    sport = request.args.get('sport', 'mlb').lower()
    history = mlb_history if sport == 'mlb' else nba_history
    return jsonify({'sport': sport, 'games': len(history), 'history': history})

@app.route('/ratings/reset', methods=['POST'])
def reset_ratings():
    global mlb_ratings, nba_ratings, mlb_history, nba_history
    mlb_ratings = dict(MLB_BASELINE)
    nba_ratings = dict(NBA_BASELINE)
    mlb_history = []
    nba_history = []
    return jsonify({'status': 'reset'})

if __name__ == '__main__':
    app.run()
