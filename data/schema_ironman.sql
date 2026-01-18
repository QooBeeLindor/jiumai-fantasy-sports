-- ========================================
-- Ironman Individual Competition Database Schema
-- ========================================
-- 根据 ironman_app.py 代码推断的表结构

-- 玩家表
CREATE TABLE IF NOT EXISTS players (
    player_id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_name TEXT NOT NULL UNIQUE,
    draft_order INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 项目状态表
CREATE TABLE IF NOT EXISTS sport_status (
    sport TEXT PRIMARY KEY,
    status TEXT NOT NULL,  -- 'active' 或 'completed'
    playoff_completed INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 玩家各项目积分表
CREATE TABLE IF NOT EXISTS ironman_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    sport TEXT NOT NULL,
    regular_rank INTEGER,
    regular_points REAL DEFAULT 0,
    playoff_points REAL DEFAULT 0,
    total_points REAL DEFAULT 0,
    is_final INTEGER DEFAULT 0,  -- 0=进行中, 1=已完成
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (player_id) REFERENCES players(player_id),
    UNIQUE(player_id, sport)
);

-- 玩家排行榜表
CREATE TABLE IF NOT EXISTS ironman_leaderboard (
    player_id INTEGER PRIMARY KEY,
    player_name TEXT NOT NULL,
    rank INTEGER NOT NULL,
    total_score REAL DEFAULT 0,
    mlb_points REAL DEFAULT 0,
    nfl_points REAL DEFAULT 0,
    nhl_points REAL DEFAULT 0,
    nba_points REAL DEFAULT 0,
    completed_sports INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (player_id) REFERENCES players(player_id)
);

-- 队名映射表（玩家在各项目的队名）
CREATE TABLE IF NOT EXISTS sport_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    sport TEXT NOT NULL,
    yahoo_team_name TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (player_id) REFERENCES players(player_id),
    UNIQUE(player_id, sport)
);

-- 初始化项目状态
INSERT OR IGNORE INTO sport_status (sport, status, playoff_completed) VALUES
('MLB', 'completed', 1),
('NFL', 'completed', 1),
('NHL', 'active', 0),
('NBA', 'active', 0);
