-- Database Schema: ironman.db
-- Tables: 9

-- Table: ironman_leaderboard
CREATE TABLE ironman_leaderboard (
    player_id INTEGER PRIMARY KEY,
    player_name TEXT NOT NULL,
    total_score REAL DEFAULT 0,           -- 总分
    rank INTEGER,                         -- 总排名
    mlb_points REAL DEFAULT 0,
    nfl_points REAL DEFAULT 0,
    nhl_points REAL DEFAULT 0,
    nba_points REAL DEFAULT 0,
    completed_sports INTEGER DEFAULT 0,   -- 已完成项目数
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (player_id) REFERENCES players(player_id)
);

-- Table: ironman_scores
CREATE TABLE ironman_scores (
    score_id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    sport TEXT NOT NULL,                  -- MLB, NFL, NHL, NBA
    regular_rank INTEGER,                 -- 常规赛排名
    regular_points REAL DEFAULT 0,        -- 常规赛得分
    playoff_rank INTEGER,                 -- 季后赛排名
    playoff_points REAL DEFAULT 0,        -- 季后赛得分
    total_points REAL DEFAULT 0,          -- 该项目总分
    is_final BOOLEAN DEFAULT 0,           -- 该项目是否已结束
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (player_id) REFERENCES players(player_id),
    UNIQUE(player_id, sport)
);

-- Table: league_standings
CREATE TABLE league_standings (
    standing_id INTEGER PRIMARY KEY AUTOINCREMENT,
    league_id TEXT NOT NULL,
    sport TEXT NOT NULL,
    yahoo_team_key TEXT NOT NULL,         -- 雅虎team_key
    yahoo_team_name TEXT,                 -- 雅虎队名
    rank INTEGER NOT NULL,                -- 当前排名
    points REAL,                          -- 积分/胜场等
    wins INTEGER,
    losses INTEGER,
    ties INTEGER,
    is_playoff BOOLEAN DEFAULT 0,         -- 是否季后赛排名
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (league_id) REFERENCES leagues(league_id),
    UNIQUE(league_id, yahoo_team_key, is_playoff)
);

-- Table: leagues
CREATE TABLE leagues (
    league_id TEXT PRIMARY KEY,            -- 雅虎League ID
    sport TEXT NOT NULL,                   -- MLB, NFL, NHL, NBA
    league_name TEXT,                      -- 联赛名称
    season TEXT DEFAULT '2024-25',
    status TEXT DEFAULT 'active',          -- active, completed
    playoff_started BOOLEAN DEFAULT 0,     -- 是否进入季后赛
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: players
CREATE TABLE players (
    player_id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_name TEXT NOT NULL UNIQUE,      -- 统一玩家名（如：GuSone, Zima等）
    draft_order INTEGER,                   -- 选秀顺位
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: scoring_rules
CREATE TABLE scoring_rules (
    rule_id INTEGER PRIMARY KEY AUTOINCREMENT,
    rank_position INTEGER NOT NULL,       -- 排名位置
    stage TEXT NOT NULL,                  -- regular (常规赛) 或 playoff (季后赛)
    points REAL NOT NULL,                 -- 积分
    UNIQUE(rank_position, stage)
);

-- Table: sport_mappings
CREATE TABLE sport_mappings (
    mapping_id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    sport TEXT NOT NULL,                   -- MLB, NFL, NHL, NBA
    yahoo_team_name TEXT,                  -- 在该项目中的雅虎队名
    yahoo_team_key TEXT,                   -- 雅虎team_key (如: nba.l.68792.t.1)
    notes TEXT,                            -- 备注
    FOREIGN KEY (player_id) REFERENCES players(player_id),
    UNIQUE(player_id, sport)
);

-- Table: sport_status
CREATE TABLE sport_status (
    sport TEXT PRIMARY KEY,               -- MLB, NFL, NHL, NBA
    status TEXT DEFAULT 'active',         -- active, completed
    playoff_completed BOOLEAN DEFAULT 0,  -- 季后赛是否结束
    last_sync TIMESTAMP
);

-- Table: sqlite_sequence
CREATE TABLE sqlite_sequence(name,seq);

