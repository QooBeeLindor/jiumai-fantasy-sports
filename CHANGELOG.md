# Changelog

All notable changes to the Jiumai Fantasy Sports project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [2.1.1] - 2026-01-24

### NBA ELO System Updates

#### Added
- **"所属联赛" (League Affiliation) column** in the main leaderboard
  - Shows which league each player belongs to (玉衡盟, 天权盟, 天玑盟, 天璇盟, 天枢盟)
  - Displayed with blue badge styling between "玩家" and "ELO" columns
  - Data sourced from `matches` table via `league_name` field

#### Fixed
- **Leagues page player detail links** 
  - Changed from hardcoded `/player/{player_id}` to `url_for('player_detail', player_id=...)`
  - Links now correctly include `/NBA/waiverleague/` prefix
  - Resolves 404 errors when clicking player details from leagues page

#### Changed
- **Backend query optimization**
  - Modified `@app.route('/')` to JOIN `matches` table for league information
  - Added `league_name` field to player data dictionary
  - No database schema changes required

#### Technical Details
- Files modified:
  - `nba_elo/app.py` - Added league_name query (3 changes)
  - `nba_elo/templates/index.html` - Added league column (2 changes)
  - `nba_elo/templates/leagues.html` - Fixed URL generation (1 change)
- Deployment: Production server (129.204.8.241)
- Status: ✅ Verified and running

---

## [2.1.0] - 2026-01-22

### NBA ELO System Major Update

#### Added
- **Complete web interface redesign**
  - Modern Bootstrap 5 UI with gradient cards
  - Responsive mobile-friendly design
  - Interactive charts using Chart.js
  
- **New pages**
  - `/` - Main ELO leaderboard with comprehensive stats
  - `/leagues` - Five league comparison dashboard
  - `/matches` - Match history with filtering
  - `/weekly_elo` - Weekly ELO progression tracking
  - `/player/<id>` - Individual player detail pages
  - `/roster/<league_id>/<team_key>` - Team roster viewing
  - `/algorithm` - ELO algorithm explanation with math formulas

- **Advanced features**
  - 11-category tie adjustment for accurate scoring
  - Dynamic K-factor based on games played
  - Peak/valley ELO tracking
  - Click-through navigation between all pages
  - Real-time data updates from Yahoo API

#### Changed
- **Database structure**
  - New `players` table with comprehensive stats
  - New `matches` table with detailed match data
  - New `leagues` table for league metadata
  - New `system_info` table for sync tracking

- **Deployment architecture**
  - Nginx reverse proxy at `/NBA/waiverleague/`
  - Gunicorn WSGI server with 2 workers
  - Supervisor process management
  - Custom middleware for path prefix handling

#### Technical Details
- Python version: 3.x
- Framework: Flask
- Database: SQLite 3
- Frontend: Bootstrap 5, Chart.js, MathJax
- Port: 5000
- URL: http://129.204.8.241/NBA/waiverleague/

---

## [2.0.0] - Earlier

### Initial Three-System Architecture

#### Added
- **NBA ELO System** (Port 5000)
  - 80 players across 5 leagues
  - Professional ELO rating algorithm
  
- **Individual Competition** (Port 5001)
  - 16 players across 4 leagues (MLB, NFL, NHL, NBA)
  - Regular season + playoff scoring
  
- **Team Competition** (Port 5002)
  - 12 teams across 5 leagues (MLB, NFL, NHL, NBA, EPL)
  - Power ranking integration

---

## Version Comparison

| Version | NBA ELO Features | Files | Changes |
|---------|------------------|-------|---------|
| 2.1.1   | + League column, Fixed links | 3 | Minor enhancements |
| 2.1.0   | Full web interface, 7 pages | 20+ | Major redesign |
| 2.0.0   | Basic ELO system | - | Initial release |

---

## Upgrade Notes

### From 2.1.0 to 2.1.1
1. Backup files: `app.py`, `index.html`, `leagues.html`
2. Replace with new versions
3. Restart service: `sudo supervisorctl restart nba_elo`
4. Verify league column appears on homepage
5. Test player links from leagues page

### From 2.0.0 to 2.1.0
1. Complete database migration required
2. New templates and static files
3. Nginx and Supervisor configuration updates
4. See `PROJECT_COMPLETION_GUIDE_v2.1.md` for details

---

## Links

- Repository: https://github.com/QooBeeLindor/jiumai-fantasy-sports
- Issues: https://github.com/QooBeeLindor/jiumai-fantasy-sports/issues
- Roadmap: [JIUMAI_FANTASY_PROJECT_ROADMAP.md](JIUMAI_FANTASY_PROJECT_ROADMAP.md)

---

## Legend

- `Added` - New features
- `Changed` - Changes in existing functionality
- `Deprecated` - Soon-to-be removed features
- `Removed` - Removed features
- `Fixed` - Bug fixes
- `Security` - Vulnerability fixes

---

**Note**: This changelog focuses on the NBA ELO System. For Individual Competition and Team Competition updates, see their respective documentation.
