import requests
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, Response
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

ODDS_KEY = '1c8ca515de9faccc4419c2152a38d0c3'
ODDS_BASE = 'https://api.the-odds-api.com/v4'
SUPABASE_URL = 'https://pghxlcghxqwkcxvwmdwh.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBnaHhsY2doeHF3a2N4dndtZHdoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ4Mzg4NjksImV4cCI6MjA5MDQxNDg2OX0.AjLfhpBXfAIMbIfcEZz_9D-ZrHjtD8QCVJOaICmNy58'
SB_HEADERS = {
    'apikey': SUPABASE_KEY,
    'Authorization': 'Bearer ' + SUPABASE_KEY,
    'Content-Type': 'application/json',
    'Prefer': 'return=representation'
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

def sb_get_ratings(sport):
    r = requests.get(
        SUPABASE_URL + '/rest/v1/ratings?sport=eq.' + sport + '&select=team,rating',
        headers=SB_HEADERS, timeout=10
    )
    if r.status_code == 200:
        return {row['team']: row['rating'] for row in r.json()}
    return {}

def sb_update_rating(sport, team, new_rating):
    requests.patch(
        SUPABASE_URL + '/rest/v1/ratings?sport=eq.' + sport + '&team=eq.' + team,
        headers=SB_HEADERS,
        json={'rating': round(new_rating, 4), 'updated_at': datetime.utcnow().isoformat()},
        timeout=10
    )

def sb_game_processed(sport, date, away, home):
    r = requests.get(
        SUPABASE_URL + '/rest/v1/processed_games?sport=eq.' + sport +
        '&game_date=eq.' + date + '&away_team=eq.' + away + '&home_team=eq.' + home + '&select=id',
        headers=SB_HEADERS, timeout=10
    )
    return r.status_code == 200 and len(r.json()) > 0

def sb_mark_processed(sport, date, away, home, away_sc, home_sc):
    requests.post(
        SUPABASE_URL + '/rest/v1/processed_games',
        headers=SB_HEADERS,
        json={'sport': sport, 'game_date': date, 'away_team': away, 'home_team': home,
              'away_score': away_sc, 'home_score': home_sc},
        timeout=10
    )

def process_game(sport, date, away, home, away_sc, home_sc, away_inj=0, home_inj=0):
    if sb_game_processed(sport, date, away, home):
        return None
    ratings = sb_get_ratings(sport)
    if away not in ratings or home not in ratings:
        return None
    away_r = ratings[away]
    home_r = ratings[home]
    hf = PARK_FACTORS.get(home, 0.10) if sport == 'mlb' else NBA_HOME
    tgpl_away = (away_sc - home_sc) + home_r - hf + away_inj
    tgpl_home = (home_sc - away_sc) + away_r + hf + home_inj
    new_away = round(0.9 * away_r + 0.1 * tgpl_away, 4)
    new_home = round(0.9 * home_r + 0.1 * tgpl_home, 4)
    sb_update_rating(sport, away, new_away)
    sb_update_rating(sport, home, new_home)
    sb_mark_processed(sport, date, away, home, away_sc, home_sc)
    return {
        'game': away + ' @ ' + home, 'score': str(away_sc) + '-' + str(home_sc),
        away: {'old': round(away_r,4), 'new': new_away},
        home: {'old': round(home_r,4), 'new': new_home}
    }

TEAM_MAP = {
    'Los Angeles Dodgers':'LAD','Toronto Blue Jays':'TOR','New York Yankees':'NYY',
    'Philadelphia Phillies':'PHI','Milwaukee Brewers':'MIL','Chicago Cubs':'CHC',
    'Boston Red Sox':'BOS','Seattle Mariners':'SEA','San Diego Padres':'SD',
    'Detroit Tigers':'DET','Texas Rangers':'TEX','Houston Astros':'HOU',
    'Cleveland Guardians':'CLE','New York Mets':'NYM','Cincinnati Reds':'CIN',
    'Kansas City Royals':'KC','Tampa Bay Rays':'TB','Arizona Diamondbacks':'AZ',
    'San Francisco Giants':'SF','Atlanta Braves':'ATL','St. Louis Cardinals':'STL',
    'Athletics':'ATH','Miami Marlins':'MIA','Baltimore Orioles':'BAL',
    'Pittsburgh Pirates':'PIT','Minnesota Twins':'MIN','Los Angeles Angels':'LAA',
    'Chicago White Sox':'CWS','Washington Nationals':'WSH','Colorado Rockies':'COL',
    'Oklahoma City Thunder':'OKC','San Antonio Spurs':'SAS','Detroit Pistons':'DET',
    'Boston Celtics':'BOS','New York Knicks':'NYK','Denver Nuggets':'DEN',
    'Cleveland Cavaliers':'CLE','Houston Rockets':'HOU','Los Angeles Lakers':'LAL',
    'Minnesota Timberwolves':'MIN','Phoenix Suns':'PHX','Charlotte Hornets':'CHA',
    'Miami Heat':'MIA','Toronto Raptors':'TOR','Atlanta Hawks':'ATL',
    'Orlando Magic':'ORL','Philadelphia 76ers':'PHI','LA Clippers':'LAC',
    'Golden State Warriors':'GSW','Portland Trail Blazers':'POR','Milwaukee Bucks':'MIL',
    'Chicago Bulls':'CHI','New Orleans Pelicans':'NOP','Memphis Grizzlies':'MEM',
    'Dallas Mavericks':'DAL','Utah Jazz':'UTA','Brooklyn Nets':'BKN',
    'Sacramento Kings':'SAC','Indiana Pacers':'IND','Washington Wizards':'WAS'
}

def team_abbr(name):
    return TEAM_MAP.get(name, name)

def auto_update(sport):
    odds_sport = 'baseball_mlb' if sport == 'mlb' else 'basketball_nba'
    r = requests.get(ODDS_BASE + '/sports/' + odds_sport + '/scores',
        params={'apiKey': ODDS_KEY, 'daysFrom': 2}, timeout=10)
    if r.status_code != 200:
        return []
    updated = []
    for game in r.json():
        if game.get('status') not in ['closed', 'complete']:
            continue
        scores = game.get('scores') or {}
        if not scores:
            continue
        away_name = game.get('away_team','')
        home_name = game.get('home_team','')
        away = team_abbr(away_name)
        home = team_abbr(home_name)
        away_sc = scores.get(away_name) or scores.get(away)
        home_sc = scores.get(home_name) or scores.get(home)
        if away_sc is None or home_sc is None:
            continue
        date = game.get('commence_time','')[:10]
        result = process_game(sport, date, away, home, int(away_sc), int(home_sc))
        if result:
            updated.append(result)
    return updated

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

@app.route('/mlb-scores')
def mlb_scores():
    try:
        r = requests.get(
            'https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard',
            timeout=10
        )
        data = r.json()
        games = []
        for event in data.get('events', []):
            comp = event.get('competitions', [{}])[0]
            competitors = comp.get('competitors', [])
            if len(competitors) < 2:
                continue
            home = next((c for c in competitors if c.get('homeAway') == 'home'), competitors[0])
            away = next((c for c in competitors if c.get('homeAway') == 'away'), competitors[1])
            status = comp.get('status', {})
            state = status.get('type', {}).get('state', 'pre')
            completed = status.get('type', {}).get('completed', False)
            period = status.get('type', {}).get('shortDetail', '')
            games.append({
                'away_team': away.get('team', {}).get('displayName', ''),
                'home_team': home.get('team', {}).get('displayName', ''),
                'away_abbr': away.get('team', {}).get('abbreviation', ''),
                'home_abbr': home.get('team', {}).get('abbreviation', ''),
                'away_score': away.get('score', '0'),
                'home_score': home.get('score', '0'),
                'status': 'inprogress' if state == 'in' else ('closed' if completed else 'scheduled'),
                'completed': completed,
                'period': period,
                'commence_time': event.get('date', '')
            })
        return jsonify(games)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/nba-scores')
def nba_scores():
    try:
        r = requests.get(
            'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard',
            timeout=10
        )
        data = r.json()
        games = []
        for event in data.get('events', []):
            comp = event.get('competitions', [{}])[0]
            competitors = comp.get('competitors', [])
            if len(competitors) < 2:
                continue
            home = next((c for c in competitors if c.get('homeAway') == 'home'), competitors[0])
            away = next((c for c in competitors if c.get('homeAway') == 'away'), competitors[1])
            status = comp.get('status', {})
            state = status.get('type', {}).get('state', 'pre')
            completed = status.get('type', {}).get('completed', False)
            period = status.get('type', {}).get('shortDetail', '')
            games.append({
                'away_team': away.get('team', {}).get('displayName', ''),
                'home_team': home.get('team', {}).get('displayName', ''),
                'away_abbr': away.get('team', {}).get('abbreviation', ''),
                'home_abbr': home.get('team', {}).get('abbreviation', ''),
                'away_score': away.get('score', '0'),
                'home_score': home.get('score', '0'),
                'status': 'inprogress' if state == 'in' else ('closed' if completed else 'scheduled'),
                'completed': completed,
                'period': period,
                'commence_time': event.get('date', '')
            })
        return jsonify(games)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/nhl-scores')
def nhl_scores():
    try:
        r = requests.get(
            'https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard',
            timeout=10
        )
        data = r.json()
        games = []
        for event in data.get('events', []):
            comp = event.get('competitions', [{}])[0]
            competitors = comp.get('competitors', [])
            if len(competitors) < 2:
                continue
            home = next((c for c in competitors if c.get('homeAway') == 'home'), competitors[0])
            away = next((c for c in competitors if c.get('homeAway') == 'away'), competitors[1])
            status = comp.get('status', {})
            state = status.get('type', {}).get('state', 'pre')
            completed = status.get('type', {}).get('completed', False)
            period = status.get('type', {}).get('shortDetail', '')
            games.append({
                'away_team': away.get('team', {}).get('displayName', ''),
                'home_team': home.get('team', {}).get('displayName', ''),
                'away_abbr': away.get('team', {}).get('abbreviation', ''),
                'home_abbr': home.get('team', {}).get('abbreviation', ''),
                'away_score': away.get('score', '0'),
                'home_score': home.get('score', '0'),
                'status': 'inprogress' if state == 'in' else ('closed' if completed else 'scheduled'),
                'completed': completed,
                'period': period,
                'commence_time': event.get('date', '')
            })
        return jsonify(games)
    except Exception as e:
        return jsonify({'error': str(e)})

def try_nba_pdf(date_str, time_str):
    url = 'https://ak-static.cms.nba.com/referee/injury/Injury-Report_' + date_str + '_' + time_str + '.pdf'
    try:
        r = requests.get(url, timeout=6)
        if r.status_code == 200:
            return url
    except Exception:
        pass
    return None

@app.route('/nba-injuries')
def nba_injuries():
    now = datetime.utcnow()
    times = ['07_15PM','06_30PM','05_30PM','04_30PM','03_30PM','02_00PM','11_00AM','09_30AM','05_00AM']
    for days_back in range(2):
        date_str = (now - timedelta(days=days_back)).strftime('%Y-%m-%d')
        for time_str in times:
            url = try_nba_pdf(date_str, time_str)
            if url:
                return jsonify({'pdf_url': url, 'date': date_str, 'time': time_str})
    return jsonify({'error': 'No injury report found'})

@app.route('/mlb-injuries')
def mlb_injuries():
    try:
        r = requests.get(
            'https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/injuries',
            timeout=10)
        data = r.json()
        injured = []
        for team in data.get('injuries', []):
            team_name = team.get('team', {}).get('abbreviation', '')
            for player in team.get('injuries', []):
                injured.append({
                    'name': player.get('athlete', {}).get('displayName', ''),
                    'team': team_name, 'status': player.get('status', ''),
                    'injury': player.get('shortComment', ''),
                    'detail': player.get('longComment', '')
                })
        injured.sort(key=lambda x: x['team'])
        return jsonify(injured)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/ratings')
def ratings():
    mlb = sb_get_ratings('mlb')
    nba = sb_get_ratings('nba')
    mlb_sorted = dict(sorted(mlb.items(), key=lambda x: x[1], reverse=True))
    nba_sorted = dict(sorted(nba.items(), key=lambda x: x[1], reverse=True))
    return jsonify({
        'last_updated': datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC'),
        'mlb': {'ratings': mlb_sorted},
        'nba': {'ratings': nba_sorted},
        'park_factors': PARK_FACTORS,
        'nba_home_court': NBA_HOME
    })

@app.route('/ratings/auto-update', methods=['POST'])
def ratings_auto_update():
    mlb_updates = auto_update('mlb')
    nba_updates = auto_update('nba')
    return jsonify({
        'status': 'ok',
        'mlb_games_processed': len(mlb_updates),
        'nba_games_processed': len(nba_updates),
        'mlb_updates': mlb_updates,
        'nba_updates': nba_updates
    })

@app.route('/ratings/update', methods=['POST'])
def update_ratings():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data'}), 400
    result = process_game(
        data.get('sport','').lower(),
        data.get('date', datetime.utcnow().strftime('%Y-%m-%d')),
        data.get('away_team','').upper(),
        data.get('home_team','').upper(),
        data.get('away_score'), data.get('home_score'),
        data.get('away_injury_adj', 0), data.get('home_injury_adj', 0)
    )
    if result:
        return jsonify({'status': 'updated', 'result': result})
    return jsonify({'status': 'skipped'})

@app.route('/ratings/history')
def ratings_history():
    sport = request.args.get('sport', 'mlb').lower()
    r = requests.get(
        SUPABASE_URL + '/rest/v1/processed_games?sport=eq.' + sport +
        '&select=game_date,away_team,home_team,away_score,home_score,processed_at' +
        '&order=processed_at.desc&limit=50',
        headers=SB_HEADERS, timeout=10)
    if r.status_code == 200:
        return jsonify({'sport': sport, 'history': r.json()})
    return jsonify({'error': 'Could not fetch history'})

DASHBOARD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta http-equiv="Content-Security-Policy" content="default-src * 'unsafe-inline' 'unsafe-eval' data: blob:;">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Walters Odds Dashboard</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500;600&display=swap');
:root{--bg:#0a0a0a;--surface:#111111;--surface2:#1a1a1a;--border:#222222;--border2:#2a2a2a;--text:#f0f0f0;--muted:#666666;--dim:#444444;--fav:#4ade80;--dog:#fb923c;--accent:#facc15;--blue:#60a5fa;--red:#f87171;--yellow:#fde68a;}
*{box-sizing:border-box;margin:0;padding:0;}
body{background:var(--bg);color:var(--text);font-family:'DM Sans',sans-serif;min-height:100vh;}
header{background:var(--surface);border-bottom:1px solid var(--border);padding:14px 20px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100;flex-wrap:wrap;gap:10px;}
.logo{font-family:'DM Mono',monospace;font-size:13px;font-weight:500;color:var(--accent);letter-spacing:0.1em;text-transform:uppercase;}
.logo span{color:var(--muted);}
.header-right{display:flex;align-items:center;gap:10px;flex-wrap:wrap;}
.sport-tabs,.view-tabs{display:flex;gap:2px;background:var(--bg);padding:2px;border-radius:8px;border:1px solid var(--border);}
.tab{font-family:'DM Mono',monospace;font-size:11px;font-weight:500;padding:5px 12px;border-radius:6px;border:none;background:transparent;color:var(--muted);cursor:pointer;letter-spacing:0.08em;transition:all 0.15s;}
.tab:hover{color:var(--text);}
.tab.active{background:var(--surface2);color:var(--accent);}
.refresh-btn{font-family:'DM Mono',monospace;font-size:11px;padding:6px 12px;border:1px solid var(--border2);border-radius:6px;background:transparent;color:var(--muted);cursor:pointer;transition:all 0.15s;}
.refresh-btn:hover{border-color:var(--accent);color:var(--accent);}
.refresh-btn:disabled{opacity:0.4;cursor:not-allowed;}
.status-dot{width:7px;height:7px;border-radius:50%;background:var(--dim);transition:background 0.3s;}
.status-dot.live{background:var(--fav);box-shadow:0 0 6px var(--fav);}
.status-dot.error{background:var(--red);}
.status-text{font-family:'DM Mono',monospace;font-size:11px;color:var(--muted);}
.main{padding:16px 20px;max-width:960px;margin:0 auto;}
.top-bar{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;flex-wrap:wrap;gap:8px;}
.game-count{font-family:'DM Mono',monospace;font-size:11px;color:var(--muted);}
.copy-all-btn{font-family:'DM Mono',monospace;font-size:10px;padding:5px 14px;border:1px solid var(--accent);border-radius:5px;background:transparent;color:var(--accent);cursor:pointer;transition:all 0.15s;}
.copy-all-btn:hover{background:rgba(250,204,21,0.08);}
.copy-all-btn.copied{border-color:var(--fav);color:var(--fav);}
.games-grid{display:flex;flex-direction:column;gap:10px;}
.game-card{background:var(--surface);border:1px solid var(--border);border-radius:10px;overflow:hidden;}
.game-card.is-live{border-color:rgba(74,222,128,0.35);}
.game-header{padding:10px 14px 8px;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:center;gap:10px;}
.matchup{font-size:13px;font-weight:500;color:var(--text);flex:1;}
.game-time{font-family:'DM Mono',monospace;font-size:11px;color:var(--muted);}
.score-badge{display:flex;align-items:center;gap:6px;background:var(--surface2);border:1px solid var(--border2);border-radius:6px;padding:3px 9px;}
.score-badge.is-live{border-color:rgba(74,222,128,0.5);background:rgba(74,222,128,0.06);}
.score-num{font-family:'DM Mono',monospace;font-size:12px;font-weight:500;color:var(--text);}
.score-lbl{font-family:'DM Mono',monospace;font-size:10px;color:var(--muted);}
.live-dot{width:6px;height:6px;border-radius:50%;background:var(--fav);box-shadow:0 0 4px var(--fav);animation:blink 1.4s infinite;}
@keyframes blink{0%,100%{opacity:1;}50%{opacity:0.3;}}
.odds-row{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;}
.odds-col{padding:9px 14px;border-right:1px solid var(--border);}
.odds-col:last-child{border-right:none;}
.col-label{font-family:'DM Mono',monospace;font-size:9px;font-weight:500;letter-spacing:0.12em;text-transform:uppercase;color:var(--dim);margin-bottom:5px;}
.team-line{display:flex;justify-content:space-between;align-items:center;padding:2px 0;}
.team-label{font-size:11px;color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1;min-width:0;margin-right:6px;}
.price{font-family:'DM Mono',monospace;font-size:12px;font-weight:500;flex-shrink:0;}
.price.fav{color:var(--fav);}
.price.dog{color:var(--dog);}
.price.neutral{color:var(--blue);}
.total-val{font-family:'DM Mono',monospace;font-size:11px;color:var(--text);padding:2px 0;}
.game-footer{padding:7px 14px;}
.copy-btn{font-family:'DM Mono',monospace;font-size:10px;padding:4px 10px;border:1px solid var(--border2);border-radius:5px;background:transparent;color:var(--muted);cursor:pointer;transition:all 0.15s;}
.copy-btn:hover{border-color:var(--accent);color:var(--accent);}
.copy-btn.copied{border-color:var(--fav);color:var(--fav);}
.loading{text-align:center;padding:50px 20px;color:var(--muted);font-family:'DM Mono',monospace;font-size:12px;}
.spinner{width:18px;height:18px;border:2px solid var(--border2);border-top-color:var(--accent);border-radius:50%;animation:spin 0.8s linear infinite;margin:0 auto 10px;}
@keyframes spin{to{transform:rotate(360deg);}}
.error-msg{text-align:center;padding:40px 20px;color:var(--red);font-family:'DM Mono',monospace;font-size:12px;line-height:2;}
.ratings-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;}
.ratings-card{background:var(--surface);border:1px solid var(--border);border-radius:10px;overflow:hidden;}
.ratings-header{padding:10px 14px;background:var(--surface2);border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:center;}
.ratings-title{font-family:'DM Mono',monospace;font-size:12px;font-weight:500;color:var(--accent);}
.ratings-subtitle{font-family:'DM Mono',monospace;font-size:10px;color:var(--muted);}
.ratings-list{padding:8px 0;}
.rating-row{display:flex;justify-content:space-between;align-items:center;padding:5px 14px;}
.rating-row:hover{background:var(--surface2);}
.rating-rank{font-family:'DM Mono',monospace;font-size:10px;color:var(--dim);width:20px;}
.rating-team{font-size:12px;font-weight:500;color:var(--text);flex:1;}
.rating-val{font-family:'DM Mono',monospace;font-size:12px;color:var(--accent);}
.inj-card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:20px 24px;}
.inj-title{font-family:'DM Mono',monospace;font-size:13px;font-weight:500;color:var(--accent);margin-bottom:8px;}
.inj-sub{font-size:12px;color:var(--muted);margin-bottom:18px;line-height:1.6;}
.inj-pdf-btn{display:inline-block;font-family:'DM Mono',monospace;font-size:12px;padding:10px 20px;border:1px solid var(--accent);border-radius:6px;background:transparent;color:var(--accent);text-decoration:none;transition:all 0.15s;}
.inj-pdf-btn:hover{background:rgba(250,204,21,0.1);}
.inj-meta{font-family:'DM Mono',monospace;font-size:11px;color:var(--dim);margin-top:10px;}
.inj-grid{display:flex;flex-direction:column;gap:6px;}
.inj-team{background:var(--surface);border:1px solid var(--border);border-radius:10px;overflow:hidden;}
.inj-team-hdr{padding:8px 14px;background:var(--surface2);border-bottom:1px solid var(--border);display:flex;gap:10px;align-items:center;}
.inj-team-name{font-family:'DM Mono',monospace;font-size:12px;font-weight:500;color:var(--accent);}
.inj-team-ct{font-family:'DM Mono',monospace;font-size:10px;color:var(--muted);}
.inj-row{padding:8px 14px;border-bottom:1px solid var(--border);display:grid;grid-template-columns:160px 110px 1fr;gap:10px;align-items:start;}
.inj-row:last-child{border-bottom:none;}
.inj-name{font-size:12px;font-weight:500;color:var(--text);}
.inj-badge{font-family:'DM Mono',monospace;font-size:10px;padding:2px 7px;border-radius:4px;display:inline-block;}
.inj-badge.out{background:rgba(248,113,113,0.15);color:var(--red);}
.inj-badge.questionable{background:rgba(253,230,138,0.15);color:var(--yellow);}
.inj-badge.probable{background:rgba(74,222,128,0.15);color:var(--fav);}
.inj-badge.doubtful{background:rgba(251,146,60,0.15);color:var(--dog);}
.inj-badge.other{background:rgba(96,165,250,0.15);color:var(--blue);}
.inj-desc{font-size:11px;color:var(--muted);line-height:1.5;}
.filter-row{display:flex;gap:6px;flex-wrap:wrap;}
.filter-btn{font-family:'DM Mono',monospace;font-size:10px;padding:4px 10px;border:1px solid var(--border2);border-radius:5px;background:transparent;color:var(--muted);cursor:pointer;transition:all 0.15s;}
.filter-btn.active{background:var(--surface2);color:var(--accent);border-color:var(--accent);}
.auto-update-bar{font-family:'DM Mono',monospace;font-size:10px;color:var(--muted);margin-bottom:12px;padding:8px 12px;background:var(--surface);border:1px solid var(--border);border-radius:6px;display:flex;justify-content:space-between;align-items:center;}
.hidden{display:none;}
@media(max-width:600px){.odds-row{grid-template-columns:1fr 1fr;}.odds-col:nth-child(2){border-right:none;}.odds-col:nth-child(3){border-top:1px solid var(--border);}.ratings-grid{grid-template-columns:1fr;}.inj-row{grid-template-columns:1fr 1fr;}.inj-desc{grid-column:1/-1;}}
</style>
</head>
<body>
<header>
  <div class="logo">Walters <span>//</span> Odds</div>
  <div class="header-right">
    <div class="sport-tabs">
      <button class="tab active" id="tab-mlb">MLB</button>
      <button class="tab" id="tab-nba">NBA</button>
      <button class="tab" id="tab-nhl">NHL</button>
    </div>
    <div class="view-tabs">
      <button class="tab active" id="view-odds">Lines</button>
      <button class="tab" id="view-ratings">Ratings</button>
      <button class="tab" id="view-inj">Injuries</button>
    </div>
    <button class="refresh-btn" id="refresh-btn">&#8635; Refresh</button>
    <div class="status-dot" id="status-dot"></div>
    <div class="status-text" id="status-text">&#8212;</div>
  </div>
</header>
<div class="main">
  <div id="odds-view">
    <div class="top-bar">
      <div class="game-count" id="game-count"></div>
      <button class="copy-all-btn" id="copy-all-btn">Copy All Lines</button>
    </div>
    <div class="games-grid" id="games-container">
      <div class="loading"><div class="spinner"></div>Loading odds...</div>
    </div>
  </div>
  <div id="ratings-view" class="hidden">
    <div class="auto-update-bar">
      <span id="ratings-update-status">Ratings update automatically on refresh</span>
      <span id="ratings-last-updated"></span>
    </div>
    <div class="ratings-grid" id="ratings-container">
      <div class="loading"><div class="spinner"></div>Loading ratings...</div>
    </div>
  </div>
  <div id="inj-view" class="hidden">
    <div id="inj-nba-wrap" class="hidden">
      <div class="inj-card" id="inj-nba-card">
        <div class="loading"><div class="spinner"></div>Finding report...</div>
      </div>
    </div>
    <div id="inj-mlb-wrap" class="hidden">
      <div class="top-bar">
        <div class="game-count" id="inj-count"></div>
        <div class="filter-row">
          <button class="filter-btn active" data-f="all">All</button>
          <button class="filter-btn" data-f="Out">Out</button>
          <button class="filter-btn" data-f="Day-To-Day">DTD</button>
        </div>
      </div>
      <div class="inj-grid" id="inj-container">
        <div class="loading"><div class="spinner"></div>Loading...</div>
      </div>
    </div>
  </div>
</div>
<script>
var sport="mlb",view="odds",filt="all",gamesList=[],injuries=[],smap={};
function fmt(p){if(p==null)return"-";var n=Math.round(p);return n>0?"+"+n:""+n;}
function fmtSp(pt,pr){if(pt==null)return"-";var s=pt>0?"+"+pt.toFixed(1):pt.toFixed(1);return pr!=null?s+"("+fmt(pr)+")":s;}
function fmtT(iso){try{return new Date(iso).toLocaleTimeString("en-US",{hour:"numeric",minute:"2-digit",timeZone:"America/Los_Angeles",timeZoneName:"short"});}catch(e){return iso;}}
function getO(os,n){if(!os)return null;for(var i=0;i<os.length;i++)if(os[i].name===n)return os[i];return null;}
function getMkt(bks,k){if(!bks)return null;for(var i=0;i<bks.length;i++){var b=bks[i];if(!b.markets)continue;for(var j=0;j<b.markets.length;j++){var m=b.markets[j];if(m.key===k&&m.outcomes&&m.outcomes.length)return m;}}return null;}
function sN(n){var p=n.split(" ");return p[p.length-1];}
function skey(a,h){return(a+"_"+h).toLowerCase().replace(/ /g,"").replace(/_/g,"");}
function buildLine(g){
  var ml=getMkt(g.bookmakers,"h2h"),sp=getMkt(g.bookmakers,"spreads"),tot=getMkt(g.bookmakers,"totals");
  var aML=ml?getO(ml.outcomes,g.away_team):null,hML=ml?getO(ml.outcomes,g.home_team):null;
  var aSP=sp?getO(sp.outcomes,g.away_team):null,hSP=sp?getO(sp.outcomes,g.home_team):null;
  var ov=tot?getO(tot.outcomes,"Over"):null,un=tot?getO(tot.outcomes,"Under"):null;
  return g.away_team+" @ "+g.home_team+" ["+fmtT(g.commence_time)+"] ML:"+(aML?fmt(aML.price):"-")+"/"+(hML?fmt(hML.price):"-")+" RL:"+(aSP?fmtSp(aSP.point,aSP.price):"-")+" / "+(hSP?fmtSp(hSP.point,hSP.price):"-")+" Total:"+(ov?"O"+ov.point+"("+fmt(ov.price)+")":"-")+" "+(un?"U"+un.point+"("+fmt(un.price)+")":"-");
}
function scoreBadge(g){
  var k=skey(g.away_team,g.home_team),sc=smap[k];
  if(!sc){
    var parts=g.away_team.split(" "),awayAbbr=parts[parts.length-1];
    parts=g.home_team.split(" ");var homeAbbr=parts[parts.length-1];
    sc=smap[skey(awayAbbr,homeAbbr)];
  }
  if(!sc)return'<div class="game-time">'+fmtT(g.commence_time)+"</div>";
  var live=sc.status==="inprogress";
  var fin=sc.completed===true||sc.status==="closed"||sc.status==="complete";
  if(!live&&!fin)return'<div class="game-time">'+fmtT(g.commence_time)+"</div>";
  var asc=sc.away_score||"0",hsc=sc.home_score||"0";
  var lbl=fin?"Final":(sc.period||"Live"),cls=live?'score-badge is-live':'score-badge',dot=live?'<div class="live-dot"></div>':"";
  return'<div class="'+cls+'">'+dot+'<span class="score-num">'+asc+" - "+hsc+'</span><span class="score-lbl">'+lbl+"</span></div>";
}
function renderGames(odds,scores){
  smap={};
  if(Array.isArray(scores))scores.forEach(function(sc){
    if(sc.away_team&&sc.home_team)smap[skey(sc.away_team,sc.home_team)]=sc;
    if(sc.away_abbr&&sc.home_abbr)smap[skey(sc.away_abbr,sc.home_abbr)]=sc;
  });
  var el=document.getElementById("games-container");
  var now=new Date(),cut=new Date(now.getTime()+40*3600000);
  var seen={};
  var up=[];
  odds.forEach(function(g){
    var t=new Date(g.commence_time);
    if(t<new Date(now.getTime()-7200000)||t>cut)return;
    var k=skey(g.away_team,g.home_team);
    if(!seen[k]){seen[k]=true;up.push(g);}
  });
  up.sort(function(a,b){return new Date(a.commence_time)-new Date(b.commence_time);});
  gamesList=up;
  document.getElementById("game-count").textContent=up.length+" games";
  if(!up.length){el.innerHTML='<div class="loading">No upcoming games.</div>';return;}
  var ll=sport==="mlb"?"Run Line":sport==="nhl"?"Puck Line":"Spread",h="";
  for(var i=0;i<up.length;i++){
    var g=up[i],as=sN(g.away_team),hs=sN(g.home_team);
    var ml=getMkt(g.bookmakers,"h2h"),sp=getMkt(g.bookmakers,"spreads"),tot=getMkt(g.bookmakers,"totals");
    var aML=ml?getO(ml.outcomes,g.away_team):null,hML=ml?getO(ml.outcomes,g.home_team):null;
    var aSP=sp?getO(sp.outcomes,g.away_team):null,hSP=sp?getO(sp.outcomes,g.home_team):null;
    var ov=tot?getO(tot.outcomes,"Over"):null,un=tot?getO(tot.outcomes,"Under"):null;
    var af=aML&&aML.price<0,hf=hML&&hML.price<0;
    var k=skey(g.away_team,g.home_team),isLive=smap[k]&&smap[k].status==="inprogress";
    h+='<div class="game-card'+(isLive?' is-live':'')+'">';
    h+='<div class="game-header"><div class="matchup">'+g.away_team+' <span style="color:var(--dim)">@</span> '+g.home_team+"</div><div>"+scoreBadge(g)+"</div></div>";
    h+='<div class="odds-row">';
    h+='<div class="odds-col"><div class="col-label">Away ML</div><div class="team-line"><span class="team-label">'+as+'</span><span class="price '+(af?"fav":"dog")+'">'+( aML?fmt(aML.price):"-")+"</span></div></div>";
    h+='<div class="odds-col"><div class="col-label">Home ML</div><div class="team-line"><span class="team-label">'+hs+'</span><span class="price '+(hf?"fav":"dog")+'">'+( hML?fmt(hML.price):"-")+"</span></div></div>";
    h+='<div class="odds-col"><div class="col-label">'+ll+'</div><div class="team-line"><span class="team-label">'+as+'</span><span class="price neutral">'+(aSP?fmtSp(aSP.point,aSP.price):"-")+'</span></div><div class="team-line"><span class="team-label">'+hs+'</span><span class="price neutral">'+(hSP?fmtSp(hSP.point,hSP.price):"-")+"</span></div></div>";
    h+='<div class="odds-col"><div class="col-label">Total</div><div class="total-val">'+(ov?"O "+ov.point+" ("+fmt(ov.price)+")":"-")+'</div><div class="total-val">'+(un?"U "+un.point+" ("+fmt(un.price)+")":"-")+"</div></div>";
    h+='</div><div class="game-footer"><button class="copy-btn" data-i="'+i+'">Copy this game</button></div></div>';
  }
  el.innerHTML=h;
  el.querySelectorAll(".copy-btn").forEach(function(b){
    b.addEventListener("click",function(){
      var idx=parseInt(this.getAttribute("data-i"));
      navigator.clipboard.writeText(buildLine(gamesList[idx])).then(function(){b.textContent="Copied!";b.classList.add("copied");setTimeout(function(){b.textContent="Copy this game";b.classList.remove("copied");},2000);});
    });
  });
}
function renderRatings(data){
  var el=document.getElementById("ratings-container");
  var mlb=data.mlb?data.mlb.ratings:{};
  var nba=data.nba?data.nba.ratings:{};
  document.getElementById("ratings-last-updated").textContent=data.last_updated||"";
  var mlbH='<div class="ratings-card"><div class="ratings-header"><span class="ratings-title">MLB Power Ratings</span><span class="ratings-subtitle">runs</span></div><div class="ratings-list">';
  var i=1;
  Object.keys(mlb).forEach(function(t){mlbH+='<div class="rating-row"><span class="rating-rank">'+i+'</span><span class="rating-team">'+t+'</span><span class="rating-val">'+mlb[t].toFixed(2)+'</span></div>';i++;});
  mlbH+="</div></div>";
  var nbaH='<div class="ratings-card"><div class="ratings-header"><span class="ratings-title">NBA Power Ratings</span><span class="ratings-subtitle">points</span></div><div class="ratings-list">';
  i=1;
  Object.keys(nba).forEach(function(t){nbaH+='<div class="rating-row"><span class="rating-rank">'+i+'</span><span class="rating-team">'+t+'</span><span class="rating-val">'+nba[t].toFixed(2)+'</span></div>';i++;});
  nbaH+="</div></div>";
  el.innerHTML=mlbH+nbaH;
}
function setStatus(state,msg){
  var d=document.getElementById("status-dot"),t=document.getElementById("status-text");
  d.className="status-dot"+(state?" "+state:"");t.textContent=msg;
}
function loadOdds(){
  setStatus("","Loading...");
  document.getElementById("games-container").innerHTML='<div class="loading"><div class="spinner"></div>Fetching odds...</div>';
  document.getElementById("game-count").textContent="";
  var ep=sport==="mlb"?"/mlb":sport==="nba"?"/nba":"/nhl";
  var sep=sport==="mlb"?"/mlb-scores":sport==="nba"?"/nba-scores":"/nhl-scores";
  var oddsData=null,scoresData=null,done=0;
  function tryRender(){done++;if(done<2)return;if(!oddsData){setStatus("error","Error");document.getElementById("games-container").innerHTML='<div class="error-msg">Could not load odds.<br>Refresh in 30s.</div>';return;}setStatus("live",new Date().toLocaleTimeString());renderGames(oddsData,scoresData||[]);}
  fetch(ep).then(function(r){return r.json();}).then(function(d){oddsData=d;tryRender();}).catch(function(){tryRender();});
  fetch(sep).then(function(r){return r.json();}).then(function(d){scoresData=d;tryRender();}).catch(function(){tryRender();});
}
function loadRatings(){
  setStatus("","Loading ratings...");
  document.getElementById("ratings-container").innerHTML='<div class="loading"><div class="spinner"></div>Loading ratings...</div>';
  document.getElementById("ratings-update-status").textContent="Checking for new results...";
  fetch("/ratings/auto-update",{method:"POST"})
    .then(function(r){return r.json();})
    .then(function(upd){
      var msg="";
      if(upd.mlb_games_processed>0||upd.nba_games_processed>0){
        msg="Updated: "+upd.mlb_games_processed+" MLB + "+upd.nba_games_processed+" NBA games";
      } else {
        msg="Ratings current — no new results";
      }
      document.getElementById("ratings-update-status").textContent=msg;
      return fetch("/ratings");
    })
    .then(function(r){return r.json();})
    .then(function(d){setStatus("live",new Date().toLocaleTimeString());renderRatings(d);})
    .catch(function(e){setStatus("error","Error");document.getElementById("ratings-container").innerHTML='<div class="error-msg">'+e+"</div>";});
}
function renderNBAInj(data){
  var el=document.getElementById("inj-nba-card");
  if(data.error){el.innerHTML='<div class="error-msg">'+data.error+"</div>";return;}
  var tl=data.time.replace("_",":").replace("PM"," PM").replace("AM"," AM");
  el.innerHTML='<div class="inj-title">Official NBA Injury Report</div><div class="inj-sub">Latest: '+data.date+" at "+tl+'</div><a class="inj-pdf-btn" href="'+data.pdf_url+'" target="_blank">Open Injury Report PDF &#8599;</a><div class="inj-meta">Source: ak-static.cms.nba.com</div>';
}
function scBadge(s){if(!s)return"other";var l=s.toLowerCase();if(l==="out")return"out";if(l.indexOf("day")>=0||l==="questionable")return"questionable";if(l==="probable")return"probable";if(l==="doubtful")return"doubtful";return"other";}
function renderMLBInj(data){injuries=data;applyFilt();}
function applyFilt(){
  var el=document.getElementById("inj-container");
  var f=filt==="all"?injuries:injuries.filter(function(p){return p.status&&p.status.toLowerCase().indexOf(filt.toLowerCase())>=0;});
  document.getElementById("inj-count").textContent=f.length+" players";
  if(!f.length){el.innerHTML='<div class="loading">No injuries matching filter.</div>';return;}
  var byT={};f.forEach(function(p){var t=p.team||"?";if(!byT[t])byT[t]=[];byT[t].push(p);});
  var teams=Object.keys(byT).sort(),h="";
  teams.forEach(function(team){
    var pl=byT[team];
    h+='<div class="inj-team"><div class="inj-team-hdr"><span class="inj-team-name">'+team+'</span><span class="inj-team-ct">'+pl.length+" player"+(pl.length>1?"s":"")+"</span></div>";
    pl.forEach(function(p){h+='<div class="inj-row"><div class="inj-name">'+(p.name||"-")+'</div><div><span class="inj-badge '+scBadge(p.status)+'">'+(p.status||"?")+'</span></div><div class="inj-desc">'+(p.injury||p.detail||"")+"</div></div>";});
    h+="</div>";
  });
  el.innerHTML=h;
}
function loadInjuries(){
  setStatus("","Loading...");
  if(sport==="nba"){
    document.getElementById("inj-nba-wrap").classList.remove("hidden");
    document.getElementById("inj-mlb-wrap").classList.add("hidden");
    document.getElementById("inj-nba-card").innerHTML='<div class="loading"><div class="spinner"></div>Finding report...</div>';
    fetch("/nba-injuries").then(function(r){return r.json();}).then(function(d){setStatus("live",new Date().toLocaleTimeString());renderNBAInj(d);}).catch(function(e){setStatus("error","Error");document.getElementById("inj-nba-card").innerHTML='<div class="error-msg">'+e+"</div>";});
  } else {
    document.getElementById("inj-nba-wrap").classList.add("hidden");
    document.getElementById("inj-mlb-wrap").classList.remove("hidden");
    document.getElementById("inj-container").innerHTML='<div class="loading"><div class="spinner"></div>Loading...</div>';
    fetch("/mlb-injuries").then(function(r){return r.json();}).then(function(d){setStatus("live",new Date().toLocaleTimeString());renderMLBInj(d);}).catch(function(e){setStatus("error","Error");document.getElementById("inj-container").innerHTML='<div class="error-msg">'+e+"</div>";});
  }
}
function loadCurrent(){
  var btn=document.getElementById("refresh-btn");
  btn.disabled=true;setTimeout(function(){btn.disabled=false;},4000);
  if(view==="odds")loadOdds();else if(view==="ratings")loadRatings();else loadInjuries();
}
function switchSport(s){sport=s;["mlb","nba","nhl"].forEach(function(x){document.getElementById("tab-"+x).className="tab"+(x===s?" active":"");});loadCurrent();}
function switchView(v){
  view=v;
  ["odds","ratings","inj"].forEach(function(x){document.getElementById("view-"+x).className="tab"+(x===v?" active":"");});
  document.getElementById("odds-view").className=v==="odds"?"":"hidden";
  document.getElementById("ratings-view").className=v==="ratings"?"":"hidden";
  document.getElementById("inj-view").className=v==="inj"?"":"hidden";
  loadCurrent();
}
document.getElementById("tab-mlb").addEventListener("click",function(){switchSport("mlb");});
document.getElementById("tab-nba").addEventListener("click",function(){switchSport("nba");});
document.getElementById("tab-nhl").addEventListener("click",function(){switchSport("nhl");});
document.getElementById("view-odds").addEventListener("click",function(){switchView("odds");});
document.getElementById("view-ratings").addEventListener("click",function(){switchView("ratings");});
document.getElementById("view-inj").addEventListener("click",function(){switchView("inj");});
document.getElementById("refresh-btn").addEventListener("click",loadCurrent);
document.getElementById("copy-all-btn").addEventListener("click",function(){
  if(!gamesList.length)return;
  var date=new Date().toLocaleDateString("en-US",{month:"short",day:"numeric",year:"numeric"});
  var text=sport.toUpperCase()+" Lines - "+date+"\\n"+gamesList.map(buildLine).join("\\n");
  var btn=this;
  navigator.clipboard.writeText(text).then(function(){btn.textContent="Copied!";btn.classList.add("copied");setTimeout(function(){btn.textContent="Copy All Lines";btn.classList.remove("copied");},2500);});
});
document.querySelectorAll(".filter-btn").forEach(function(b){
  b.addEventListener("click",function(){document.querySelectorAll(".filter-btn").forEach(function(x){x.classList.remove("active");});this.classList.add("active");filt=this.getAttribute("data-f");applyFilt();});
});
loadOdds();
</script>
</body>
</html>"""

@app.route('/')
def dashboard():
    resp = Response(DASHBOARD, mimetype='text/html')
    resp.headers['Content-Security-Policy'] = "default-src * 'unsafe-inline' 'unsafe-eval' data: blob:;"
    return resp

if __name__ == '__main__':
    app.run()
