-- Database Schema: irongroup.db
-- Tables: 6

-- Table: leagues
CREATE TABLE leagues (
    league_id TEXT PRIMARY KEY,
    sport TEXT NOT NULL,      -- MLB/NFL/NHL/NBA/EPL
    platform TEXT NOT NULL,   -- Yahoo/Fantrax
    status TEXT NOT NULL,     -- active/completed
    yahoo_league_id TEXT,     -- Yahoo联赛ID（如果是Yahoo）
    fantrax_league_id TEXT,   -- Fantrax联赛ID（如果是Fantrax）
    updated_at TIMESTAMP
);

-- Table: sqlite_sequence
CREATE TABLE sqlite_sequence(name,seq);

-- Table: team_leaderboard
CREATE TABLE team_leaderboard (
    team_id INTEGER PRIMARY KEY,
    team_name TEXT NOT NULL,
    rank INTEGER,
    total_score REAL DEFAULT 0,
    mlb_score REAL DEFAULT 0,
    nfl_score REAL DEFAULT 0,
    nhl_score REAL DEFAULT 0,
    nba_score REAL DEFAULT 0,
    epl_score REAL DEFAULT 0,
    completed_sports INTEGER DEFAULT 0,  -- 已完成项目数
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);

-- Table: team_members
CREATE TABLE team_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL,
    member_name TEXT NOT NULL,
    FOREIGN KEY (team_id) REFERENCES teams(team_id),
    UNIQUE(team_id, member_name)
);

-- Table: team_scores
CREATE TABLE team_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL,
    league_id TEXT NOT NULL,
    sport TEXT NOT NULL,
    playoff_rank INTEGER,          -- 季后赛排名
    playoff_score REAL DEFAULT 0,  -- 季后赛积分
    regular_bonus REAL DEFAULT 0,  -- 常规赛加分
    power_rank INTEGER,            -- 实力榜排名（进行中联赛）
    total_score REAL DEFAULT 0,    -- 项目总分 = playoff_score + regular_bonus
    is_final INTEGER DEFAULT 0,    -- 是否最终得分（0=进行中，1=已完成）
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (team_id) REFERENCES teams(team_id),
    FOREIGN KEY (league_id) REFERENCES leagues(league_id),
    UNIQUE(team_id, league_id)
);

-- Table: teams
CREATE TABLE teams (
    team_id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

