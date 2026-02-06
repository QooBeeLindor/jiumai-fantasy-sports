-- 九麦NBA蛇形选秀联赛数据库Schema
-- 版本: 2.0 (移除ELO系统)
-- 日期: 2025-02-03

-- ============================================================================
-- 核心表
-- ============================================================================

-- 联赛表
CREATE TABLE IF NOT EXISTS leagues (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    tier INTEGER NOT NULL,
    yahoo_id TEXT UNIQUE NOT NULL,
    league_key TEXT NOT NULL,
    season INTEGER NOT NULL,
    teams_count INTEGER DEFAULT 16,
    promotion_slots INTEGER DEFAULT 0,
    relegation_slots INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 玩家表（移除elo_rating字段）
CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    yahoo_guid TEXT NOT NULL UNIQUE,
    unified_name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_players_yahoo_guid ON players(yahoo_guid);

-- ============================================================================
-- 选秀相关
-- ============================================================================

-- 选秀记录表
CREATE TABLE IF NOT EXISTS draft_picks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    league_id INTEGER NOT NULL,
    season INTEGER NOT NULL,
    draft_position INTEGER NOT NULL,
    round_num INTEGER NOT NULL,
    pick_in_round INTEGER NOT NULL,
    player_id INTEGER NOT NULL,
    yahoo_player_id TEXT NOT NULL,
    nba_player_name TEXT NOT NULL,
    nba_position TEXT,
    nba_team TEXT,
    FOREIGN KEY (league_id) REFERENCES leagues(id),
    FOREIGN KEY (player_id) REFERENCES players(id),
    UNIQUE(league_id, season, draft_position)
);

CREATE INDEX IF NOT EXISTS idx_draft_picks_league ON draft_picks(league_id, season);
CREATE INDEX IF NOT EXISTS idx_draft_picks_player ON draft_picks(player_id, season);

-- ADP排行榜（季初计算一次）
CREATE TABLE IF NOT EXISTS adp_rankings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    season INTEGER NOT NULL,
    rank INTEGER NOT NULL,
    yahoo_player_id TEXT NOT NULL,
    nba_player_name TEXT NOT NULL,
    nba_position TEXT,
    nba_team TEXT,
    adp REAL NOT NULL,
    times_drafted INTEGER NOT NULL,
    best_pick INTEGER NOT NULL,
    worst_pick INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(season, yahoo_player_id)
);

CREATE INDEX IF NOT EXISTS idx_adp_season ON adp_rankings(season, rank);

-- ============================================================================
-- 比赛相关
-- ============================================================================

-- 比赛记录表
CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    league_id INTEGER NOT NULL,
    season INTEGER NOT NULL,
    week INTEGER NOT NULL,
    player1_id INTEGER NOT NULL,
    player2_id INTEGER NOT NULL,
    score1 REAL NOT NULL,
    score2 REAL NOT NULL,
    winner_id INTEGER,
    is_playoffs BOOLEAN DEFAULT 0,
    match_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (league_id) REFERENCES leagues(id),
    FOREIGN KEY (player1_id) REFERENCES players(id),
    FOREIGN KEY (player2_id) REFERENCES players(id),
    FOREIGN KEY (winner_id) REFERENCES players(id)
);

CREATE INDEX IF NOT EXISTS idx_matches_league_week ON matches(league_id, week, season);
CREATE INDEX IF NOT EXISTS idx_matches_players ON matches(player1_id, player2_id);

-- 联赛战绩统计
CREATE TABLE IF NOT EXISTS league_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    league_id INTEGER NOT NULL,
    season INTEGER NOT NULL,
    matches_played INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    ties INTEGER DEFAULT 0,
    FOREIGN KEY (player_id) REFERENCES players(id),
    FOREIGN KEY (league_id) REFERENCES leagues(id),
    UNIQUE(player_id, league_id, season)
);

CREATE INDEX IF NOT EXISTS idx_league_stats ON league_stats(player_id, league_id, season);

-- ============================================================================
-- Roto积分系统（新增）
-- ============================================================================

-- 各联盟Roto积分
CREATE TABLE IF NOT EXISTS roto_standings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    league_id INTEGER NOT NULL,
    player_id INTEGER NOT NULL,
    season INTEGER NOT NULL,
    week INTEGER NOT NULL,
    roto_points REAL NOT NULL,
    rank INTEGER NOT NULL,
    -- 11项统计排名
    fgm_rank INTEGER,
    fgp_rank INTEGER,
    ftm_rank INTEGER,
    ftp_rank INTEGER,
    tpm_rank INTEGER,
    pts_rank INTEGER,
    reb_rank INTEGER,
    ast_rank INTEGER,
    stl_rank INTEGER,
    blk_rank INTEGER,
    to_rank INTEGER,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (league_id) REFERENCES leagues(id),
    FOREIGN KEY (player_id) REFERENCES players(id),
    UNIQUE(league_id, player_id, season, week)
);

CREATE INDEX IF NOT EXISTS idx_roto_league_week ON roto_standings(league_id, week, season);
CREATE INDEX IF NOT EXISTS idx_roto_player ON roto_standings(player_id, season);

-- 全盟Roto排行榜
CREATE TABLE IF NOT EXISTS overall_roto_rankings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    season INTEGER NOT NULL,
    week INTEGER NOT NULL,
    total_roto_points REAL NOT NULL,
    overall_rank INTEGER NOT NULL,
    leagues_count INTEGER NOT NULL,
    avg_roto_points REAL NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (player_id) REFERENCES players(id),
    UNIQUE(player_id, season, week)
);

CREATE INDEX IF NOT EXISTS idx_overall_roto ON overall_roto_rankings(season, week, overall_rank);

-- ============================================================================
-- 交易相关
-- ============================================================================

-- FA交易记录（ADD/DROP）
CREATE TABLE IF NOT EXISTS fa_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    league_id INTEGER NOT NULL,
    player_id INTEGER NOT NULL,
    nba_player_key TEXT NOT NULL,
    nba_player_name TEXT NOT NULL,
    transaction_type TEXT NOT NULL CHECK(transaction_type IN ('ADD', 'DROP')),
    transaction_date TIMESTAMP NOT NULL,
    season INTEGER NOT NULL,
    FOREIGN KEY (league_id) REFERENCES leagues(id),
    FOREIGN KEY (player_id) REFERENCES players(id)
);

CREATE INDEX IF NOT EXISTS idx_fa_transactions_player ON fa_transactions(nba_player_key, transaction_type);
CREATE INDEX IF NOT EXISTS idx_fa_transactions_date ON fa_transactions(transaction_date);

-- FA球员排行榜（定期更新）
CREATE TABLE IF NOT EXISTS fa_rankings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    yahoo_player_id TEXT NOT NULL,
    nba_player_name TEXT NOT NULL,
    season INTEGER NOT NULL,
    week INTEGER NOT NULL,
    add_count INTEGER DEFAULT 0,
    drop_count INTEGER DEFAULT 0,
    total_transactions INTEGER DEFAULT 0,
    net_adds INTEGER DEFAULT 0,  -- ADD - DROP
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(yahoo_player_id, season, week)
);

CREATE INDEX IF NOT EXISTS idx_fa_rankings ON fa_rankings(season, week);

-- ============================================================================
-- 记录簿
-- ============================================================================

-- 记录簿
CREATE TABLE IF NOT EXISTS record_book (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_type TEXT NOT NULL,
    record_name TEXT NOT NULL,
    record_value REAL NOT NULL,
    player_id INTEGER,
    league_id INTEGER,
    season INTEGER,
    week INTEGER,
    additional_info TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (player_id) REFERENCES players(id),
    FOREIGN KEY (league_id) REFERENCES leagues(id)
);

CREATE INDEX IF NOT EXISTS idx_record_type ON record_book(record_type, record_value DESC);

-- ============================================================================
-- 历史存档
-- ============================================================================

-- 赛季存档
CREATE TABLE IF NOT EXISTS season_archive (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    season INTEGER UNIQUE NOT NULL,
    end_date DATE,
    total_players INTEGER,
    total_matches INTEGER,
    champion_id INTEGER,
    archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (champion_id) REFERENCES players(id)
);

-- 荣誉记录
CREATE TABLE IF NOT EXISTS honors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    league_id INTEGER NOT NULL,
    season INTEGER NOT NULL,
    honor_type TEXT NOT NULL CHECK(honor_type IN ('CHAMPION', 'RUNNER_UP', 'THIRD_PLACE', 'PROMOTION', 'RELEGATION')),
    rank INTEGER,
    points REAL,
    FOREIGN KEY (player_id) REFERENCES players(id),
    FOREIGN KEY (league_id) REFERENCES leagues(id)
);

CREATE INDEX IF NOT EXISTS idx_honors_player ON honors(player_id, season);

-- ============================================================================
-- 系统管理
-- ============================================================================

-- 同步日志
CREATE TABLE IF NOT EXISTS sync_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    league_id INTEGER,
    season INTEGER,
    sync_type TEXT NOT NULL,
    last_synced_week INTEGER,
    sync_status TEXT CHECK(sync_status IN ('SUCCESS', 'FAILED', 'PARTIAL')),
    error_message TEXT,
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (league_id) REFERENCES leagues(id)
);

CREATE INDEX IF NOT EXISTS idx_sync_logs ON sync_logs(league_id, season, synced_at DESC);
