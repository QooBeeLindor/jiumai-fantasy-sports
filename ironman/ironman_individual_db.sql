-- ============================================================================
-- 铁人个人赛积分系统 - 独立数据库设计
-- 版本：v2.0 (简化版)
-- 创建日期：2026-01-11
-- 数据库：ironman.db (独立，不混入nba_elo.db)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. 玩家基础信息表
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS players (
    player_id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_name TEXT NOT NULL UNIQUE,      -- 统一玩家名（如：GuSone, Zima等）
    draft_order INTEGER,                   -- 选秀顺位
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 2. 玩家跨联赛队名映射表 (核心！解决队名不一致问题)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sport_mappings (
    mapping_id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    sport TEXT NOT NULL,                   -- MLB, NFL, NHL, NBA
    yahoo_team_name TEXT,                  -- 在该项目中的雅虎队名
    yahoo_team_key TEXT,                   -- 雅虎team_key (如: nba.l.68792.t.1)
    notes TEXT,                            -- 备注
    FOREIGN KEY (player_id) REFERENCES players(player_id),
    UNIQUE(player_id, sport)
);

-- ----------------------------------------------------------------------------
-- 3. 联赛信息表
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS leagues (
    league_id TEXT PRIMARY KEY,            -- 雅虎League ID
    sport TEXT NOT NULL,                   -- MLB, NFL, NHL, NBA
    league_name TEXT,                      -- 联赛名称
    season TEXT DEFAULT '2024-25',
    status TEXT DEFAULT 'active',          -- active, completed
    playoff_started BOOLEAN DEFAULT 0,     -- 是否进入季后赛
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 4. 当前联赛排名表 (从雅虎API获取)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS league_standings (
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

-- ----------------------------------------------------------------------------
-- 5. 积分规则表
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS scoring_rules (
    rule_id INTEGER PRIMARY KEY AUTOINCREMENT,
    rank_position INTEGER NOT NULL,       -- 排名位置
    stage TEXT NOT NULL,                  -- regular (常规赛) 或 playoff (季后赛)
    points REAL NOT NULL,                 -- 积分
    UNIQUE(rank_position, stage)
);

-- 初始化积分规则
INSERT OR IGNORE INTO scoring_rules (rank_position, stage, points) VALUES
-- 常规赛积分 (1-16名)
(1, 'regular', 16),
(2, 'regular', 15),
(3, 'regular', 14),
(4, 'regular', 13),
(5, 'regular', 12),
(6, 'regular', 11),
(7, 'regular', 10),
(8, 'regular', 9),
(9, 'regular', 8),
(10, 'regular', 7),
(11, 'regular', 6),
(12, 'regular', 5),
(13, 'regular', 4),
(14, 'regular', 3),
(15, 'regular', 2),
(16, 'regular', 1),
-- 季后赛积分 (前5名)
(1, 'playoff', 3),
(2, 'playoff', 2),
(3, 'playoff', 1),
(4, 'playoff', 0.5),
(5, 'playoff', 0.5);

-- ----------------------------------------------------------------------------
-- 6. 铁人积分明细表
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ironman_scores (
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

-- ----------------------------------------------------------------------------
-- 7. 铁人总排行榜表
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ironman_leaderboard (
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

-- ----------------------------------------------------------------------------
-- 8. 项目状态表 (方便判断哪些项目已结束)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sport_status (
    sport TEXT PRIMARY KEY,               -- MLB, NFL, NHL, NBA
    status TEXT DEFAULT 'active',         -- active, completed
    playoff_completed BOOLEAN DEFAULT 0,  -- 季后赛是否结束
    last_sync TIMESTAMP
);

-- 初始化项目状态（根据Excel数据）
INSERT OR IGNORE INTO sport_status (sport, status, playoff_completed) VALUES
('MLB', 'completed', 1),   -- 已结束
('NFL', 'completed', 1),   -- 已结束
('NHL', 'active', 0),      -- 进行中
('NBA', 'active', 0);      -- 进行中

-- ----------------------------------------------------------------------------
-- 索引优化
-- ----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_standings_lookup 
    ON league_standings(league_id, rank);

CREATE INDEX IF NOT EXISTS idx_mapping_lookup 
    ON sport_mappings(player_id, sport);

CREATE INDEX IF NOT EXISTS idx_scores_player 
    ON ironman_scores(player_id);

-- ----------------------------------------------------------------------------
-- 视图：铁人排行榜（便捷查询）
-- ----------------------------------------------------------------------------
CREATE VIEW IF NOT EXISTS v_ironman_ranking AS
SELECT 
    l.rank,
    l.player_name,
    l.total_score,
    l.mlb_points,
    l.nfl_points,
    l.nhl_points,
    l.nba_points,
    l.completed_sports,
    l.updated_at
FROM ironman_leaderboard l
ORDER BY l.rank;

-- ----------------------------------------------------------------------------
-- 触发器：自动更新总排行榜排名
-- ----------------------------------------------------------------------------
CREATE TRIGGER IF NOT EXISTS update_ironman_rank
AFTER UPDATE OF total_score ON ironman_leaderboard
BEGIN
    UPDATE ironman_leaderboard
    SET rank = (
        SELECT COUNT(*) + 1
        FROM ironman_leaderboard l2
        WHERE l2.total_score > NEW.total_score
    )
    WHERE player_id = NEW.player_id;
END;

-- ============================================================================
-- 使用说明
-- ============================================================================
-- 
-- 1. 创建独立数据库：
--    sqlite3 ironman.db < ironman_individual_db.sql
--
-- 2. 核心工作流程：
--    a) 从雅虎API获取各项目排名 → league_standings
--    b) 通过sport_mappings映射玩家
--    c) 根据scoring_rules计算积分 → ironman_scores
--    d) 汇总更新 → ironman_leaderboard
--
-- 3. 关键查询：
--    -- 查看总排行
--    SELECT * FROM v_ironman_ranking;
--    
--    -- 查看某玩家各项积分
--    SELECT * FROM ironman_scores WHERE player_id = 1;
--    
--    -- 查看玩家队名映射
--    SELECT p.player_name, m.sport, m.yahoo_team_name 
--    FROM players p
--    JOIN sport_mappings m ON p.player_id = m.player_id
--    WHERE p.player_name = 'GuSone';
--
-- ============================================================================
