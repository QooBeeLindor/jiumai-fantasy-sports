-- ========================================
-- NBA ELO System Database Schema
-- NBA范特西联赛ELO评分系统数据库结构
-- ========================================

-- 球员表
CREATE TABLE IF NOT EXISTS players (
    player_id TEXT PRIMARY KEY,
    yahoo_guid TEXT UNIQUE,
    nickname TEXT,
    current_elo REAL DEFAULT 1500,
    initial_elo REAL DEFAULT 1500,
    games_played INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    ties INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 比赛记录表
CREATE TABLE IF NOT EXISTS matches (
    match_id TEXT PRIMARY KEY,
    league_id TEXT,
    league_name TEXT,
    week INTEGER,
    season INTEGER,
    team1_id TEXT,
    team1_manager_id TEXT,
    team1_score REAL,
    team1_elo_before REAL,
    team1_elo_after REAL,
    team2_id TEXT,
    team2_manager_id TEXT,
    team2_score REAL,
    team2_elo_before REAL,
    team2_elo_after REAL,
    result TEXT,
    match_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (team1_manager_id) REFERENCES players(player_id),
    FOREIGN KEY (team2_manager_id) REFERENCES players(player_id)
);

-- 联赛信息表
CREATE TABLE IF NOT EXISTS leagues (
    league_id TEXT PRIMARY KEY,
    league_name TEXT,
    season INTEGER,
    level INTEGER,
    num_teams INTEGER,
    current_week INTEGER,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 系统信息表（记录数据更新时间）
CREATE TABLE IF NOT EXISTS system_info (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 初始化5个联赛（北斗五星）
INSERT OR IGNORE INTO leagues (league_id, league_name, season, num_teams) VALUES
('161296', '【九麦竞价】25-26 天玑盟', 2025, 16),
('161314', '天枢盟', 2025, 16),
('161323', '九麦天璇盟', 2025, 16),
('162271', '九麦NBA天权盟', 2025, 16),
('162274', '九麦玉衡盟', 2025, 16);

-- 创建索引优化查询
CREATE INDEX IF NOT EXISTS idx_players_elo ON players(current_elo DESC);
CREATE INDEX IF NOT EXISTS idx_players_guid ON players(yahoo_guid);
CREATE INDEX IF NOT EXISTS idx_matches_week ON matches(week);
CREATE INDEX IF NOT EXISTS idx_matches_league ON matches(league_id);
CREATE INDEX IF NOT EXISTS idx_matches_manager1 ON matches(team1_manager_id);
CREATE INDEX IF NOT EXISTS idx_matches_manager2 ON matches(team2_manager_id);
