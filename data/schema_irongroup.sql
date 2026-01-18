-- ========================================
-- Ironman Team Competition Database Schema
-- ========================================
-- 根据 irongroup_app.py 代码推断的表结构

-- 团队表
CREATE TABLE IF NOT EXISTS teams (
    team_id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 团队成员表
CREATE TABLE IF NOT EXISTS team_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL,
    member_name TEXT NOT NULL,
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);

-- 联赛表
CREATE TABLE IF NOT EXISTS leagues (
    league_id TEXT PRIMARY KEY,
    sport TEXT NOT NULL,
    status TEXT NOT NULL,  -- 'active' 或 'completed'
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 团队各项目积分表
CREATE TABLE IF NOT EXISTS team_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL,
    league_id TEXT NOT NULL,
    sport TEXT NOT NULL,
    playoff_rank INTEGER,
    playoff_score REAL DEFAULT 0,
    regular_bonus REAL DEFAULT 0,
    total_score REAL DEFAULT 0,
    power_rank INTEGER,  -- 实力榜排名（用于计算预期得分）
    is_final INTEGER DEFAULT 0,  -- 0=进行中, 1=已完成
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (team_id) REFERENCES teams(team_id),
    FOREIGN KEY (league_id) REFERENCES leagues(league_id),
    UNIQUE(team_id, league_id, sport)
);

-- 团队排行榜表
CREATE TABLE IF NOT EXISTS team_leaderboard (
    team_id INTEGER PRIMARY KEY,
    team_name TEXT NOT NULL,
    rank INTEGER NOT NULL,
    total_score REAL DEFAULT 0,
    mlb_score REAL DEFAULT 0,
    nfl_score REAL DEFAULT 0,
    nhl_score REAL DEFAULT 0,
    nba_score REAL DEFAULT 0,
    epl_score REAL DEFAULT 0,
    completed_sports INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);

-- 初始化联赛数据
INSERT OR IGNORE INTO leagues (league_id, sport, status) VALUES
('team_mlb', 'MLB', 'completed'),
('team_nfl', 'NFL', 'completed'),
('team_nhl', 'NHL', 'active'),
('team_nba', 'NBA', 'active'),
('team_epl', 'EPL', 'active');

-- 初始化12个团队数据
INSERT OR IGNORE INTO teams (team_name) VALUES
('鱼跃本垒'),
('槑赛德斯崩驰'),
('口味虾'),
('JB章日虾.Going'),
('Spurs No.1 in CNY'),
('三拒投'),
('我们的偶像是魔球理论人'),
('揍魔王'),
('forever1'),
('奥特鹅'),
('二次元小猪'),
('茶岩蛋');

-- 初始化团队成员（需要根据实际情况填充）
-- 示例：
-- INSERT OR IGNORE INTO team_members (team_id, member_name) 
-- SELECT team_id, '成员名' FROM teams WHERE team_name = '团队名';
