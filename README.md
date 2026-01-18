# 🏆 Ironman Fantasy Sports System - Three Systems Architecture

A comprehensive fantasy sports platform featuring **three independent systems**: NBA ELO Rating System, Individual Competition, and Team Competition.

## ⭐ Three Systems Overview

### 1. NBA ELO System (Port 5000)
- 5 leagues (80 teams, 80 players)
- Professional ELO rating algorithm
- 11-category tie adjustment
- Dynamic K-factor
- Weekly ELO tracking
- Algorithm explanation with math formulas
- Team roster viewing

### 2. Individual Competition (Port 5001)
- 16 players competing across 4 leagues (MLB, NFL, NHL, NBA)
- Regular season + playoff scoring
- Real-time rankings and statistics
- Player detail pages

### 3. Team Competition (Port 5002)
- 12 teams competing across 5 leagues (MLB, NFL, NHL, NBA, EPL)
- Power ranking integration
- Expected scores for ongoing leagues
- Team member tracking

## Features

### Individual Competition
- 16 players competing across 4 leagues (MLB, NFL, NHL, NBA)
- Regular season + playoff scoring
- Real-time rankings and statistics
- Player detail pages with complete history

### Team Competition
- 12 teams competing across 5 leagues (MLB, NFL, NHL, NBA, EPL)
- Power ranking integration
- Expected scores for ongoing leagues
- Team member tracking

## Tech Stack

- **Backend**: Python 3, Flask
- **Database**: SQLite 3
- **Frontend**: HTML5, Bootstrap 5, Chart.js, MathJax
- **Deployment**: Nginx, Gunicorn, Supervisor
- **Data Source**: Yahoo Fantasy API

## System Comparison

| Feature | NBA ELO | Individual | Team |
|---------|---------|------------|------|
| Scale | 80 players/5 leagues | 16 players/4 leagues | 12 teams/5 leagues |
| Scoring | ELO rating | Fixed rules | Fixed rules |
| Routes | 7 | 3 | 5 |
| Templates | 8 | 3 | 3 |
| DB Tables | 4 | 9 | 6 |
| Port | 5000 | 5001 | 5002 |

## Quick Start

### Prerequisites
```bash
Python 3.8+
pip
virtualenv (recommended)
```

### Installation
```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/ironman-fantasy-sports.git
cd ironman-fantasy-sports

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize databases
cd ironman && sqlite3 ironman.db < ../data/schema_ironman.sql
cd ../irongroup && sqlite3 irongroup.db < ../data/schema_irongroup.sql

# Configure
cp config.example.py config.py
# Edit config.py with your Yahoo API credentials

# Run
python ironman/ironman_app.py  # Individual competition on port 5000
python irongroup/irongroup_app.py  # Team competition on port 5002
```

## Project Structure

```
ironman-fantasy-sports/
├── ironman/               # Individual competition
│   ├── ironman_app.py
│   ├── sync_yahoo_standings.py
│   └── templates/
├── irongroup/             # Team competition
│   ├── irongroup_app.py
│   ├── sync_team_yahoo_simple.py
│   └── templates/
├── data/                  # Database schemas
├── deployment/            # Nginx/Supervisor configs
└── docs/                  # Documentation
```

## Documentation

- **For New AI Assistants**: `docs/FOR_NEW_CONVERSATIONS.md`
- **Complete Technical Doc**: `docs/项目完整文档_新对话专用.md`
- **Maintenance Guide**: `docs/维护指南_v2.0.md`
- **Code Reference**: `docs/CODE_REFERENCE.md`

## Usage

### Sync Data from Yahoo
```bash
# Individual competition
cd ironman
python sync_yahoo_standings.py

# Team competition
cd irongroup
python sync_team_yahoo_simple.py irongroup.db oauth2.json
```

### Access Web Interface
- Individual: `http://localhost:5000/ironman/individual`
- Team: `http://localhost:5002/irongroup/leaderboard`

## Deployment

See `deployment/` directory for:
- Nginx reverse proxy configuration
- Supervisor process management
- Automated deployment script

## API

### Individual Competition
```bash
GET /api/leaderboard
# Returns JSON with all players and scores
```

### Team Competition
```bash
GET /irongroup/api/leaderboard
# Returns JSON with all teams and scores
```

## Contributing

This is a private project for Jiumai Fantasy League. Contributions are welcome from league members.

## License

MIT License - See LICENSE file

## Roadmap

### Short-term (1-2 weeks)
- [ ] Complete EPL data sync
- [ ] Migrate irongroup to Supervisor
- [ ] Add SSL/HTTPS support

### Mid-term (1-2 months)
- [ ] Web admin panel
- [ ] Automated data sync (cron jobs)
- [ ] Data visualization charts

### Long-term (3-6 months)
- [ ] Mobile app
- [ ] Real-time push notifications
- [ ] User authentication system

## Support

For issues or questions, please contact the league administrator.
