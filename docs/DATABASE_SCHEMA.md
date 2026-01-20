# 数据库结构文档

## 📊 irongroup.db (铁人团队赛)

### 表结构

#### 1. teams (团队表)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| team_id | INTEGER | PRIMARY KEY | 团队ID |
| team_name | TEXT | NOT NULL | 团队名称 |
| created_at | TIMESTAMP | | 创建时间 |

**示例数据:**
```sql
team_id | team_name
--------|----------
1       | 槑赛德斯崩驰
2       | 口味虾
3       | 三拒投
...
```

---

#### 2. team_members (团队成员表)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PRIMARY KEY | 记录ID |
| team_id | INTEGER | NOT NULL, FOREIGN KEY | 团队ID |
| member_name | TEXT | NOT NULL | 成员名称 |

**示例数据:**
```sql
id | team_id | member_name
---|---------|------------
1  | 2       | CR7
2  | 2       | QB
3  | 2       | 虾酱
```

---

#### 3. leagues (联赛表)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| league_id | TEXT | PRIMARY KEY | 联赛ID |
| sport | TEXT | NOT NULL | 联赛名称 (MLB/NFL/NHL/NBA/EPL) |
| platform | TEXT | NOT NULL | 平台 (Yahoo/Fantrax) |
| status | TEXT | NOT NULL | 状态 (active/completed) |
| yahoo_league_id | TEXT | | Yahoo联赛ID |
| fantrax_league_id | TEXT | | Fantrax联赛ID |
| updated_at | TIMESTAMP | | 更新时间 |

**示例数据:**
```sql
league_id  | sport | platform | status
-----------|-------|----------|--------
team_nhl   | NHL   | Yahoo    | active
team_nba   | NBA   | Yahoo    | active
team_epl   | EPL   | Fantrax  | active
team_mlb   | MLB   | Yahoo    | completed
team_nfl   | NFL   | Yahoo    | completed
```

---

#### 4. team_scores (团队积分表) ⭐核心表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PRIMARY KEY | 记录ID |
| team_id | INTEGER | NOT NULL, FOREIGN KEY | 团队ID |
| league_id | TEXT | NOT NULL, FOREIGN KEY | 联赛ID |
| sport | TEXT | NOT NULL | 联赛名称 |
| playoff_rank | INTEGER | | 季后赛排名 (1-12) |
| playoff_score | REAL | | 季后赛积分 (3-13分) |
| regular_bonus | REAL | | 常规赛bonus (0-3分) |
| power_rank | INTEGER | | 实力榜排名 (用于预期积分) |
| total_score | REAL | | 总分 (bonus + playoff) |
| is_final | INTEGER | | 是否完成 (0/1) |
| updated_at | TIMESTAMP | | 更新时间 |

**字段说明:**

- **power_rank**: 每周同步Yahoo实力榜排名，用于计算预期季后赛积分
- **regular_bonus**: 常规赛结束时更新，只有前4名有分 (3, 2, 1, 0.5)
- **playoff_score**: 季后赛结束时更新，全部12队都有 (13-3分)
- **total_score**: 自动计算 = regular_bonus + playoff_score
- **is_final**: 季后赛结束时设为1，表示该联赛已完成

**示例数据 - EPL常规赛结束，季后赛未开始:**
```sql
team_id | sport | power_rank | regular_bonus | playoff_score | total_score | is_final
--------|-------|------------|---------------|---------------|-------------|----------
2       | EPL   | 1          | 3.0           | NULL          | 3.0         | 0
8       | EPL   | 2          | 2.0           | NULL          | 2.0         | 0
11      | EPL   | 3          | 1.0           | NULL          | 1.0         | 0
4       | EPL   | 4          | 0.5           | NULL          | 0.5         | 0
1       | EPL   | 5          | 0.0           | NULL          | 0.0         | 0
```

**示例数据 - MLB全部结束:**
```sql
team_id | sport | playoff_rank | playoff_score | regular_bonus | total_score | is_final
--------|-------|--------------|---------------|---------------|-------------|----------
2       | MLB   | 1            | 13.0          | 3.0           | 16.0        | 1
8       | MLB   | 5            | 9.0           | 2.0           | 11.0        | 1
11      | MLB   | 8            | 7.0           | 0.0           | 7.0         | 1
```

---

#### 5. team_leaderboard (团队排行榜) - 汇总表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| team_id | INTEGER | PRIMARY KEY, FOREIGN KEY | 团队ID |
| team_name | TEXT | NOT NULL | 团队名称 |
| rank | INTEGER | | 总排名 |
| total_score | REAL | | 总分 (所有联赛) |
| mlb_score | REAL | | MLB积分 |
| nfl_score | REAL | | NFL积分 |
| nhl_score | REAL | | NHL积分 |
| nba_score | REAL | | NBA积分 |
| epl_score | REAL | | EPL积分 |
| completed_sports | INTEGER | | 已完成项目数 |
| updated_at | TIMESTAMP | | 更新时间 |

**说明:** 这是汇总表，通过Python脚本从team_scores计算生成。

**示例数据:**
```sql
team_id | team_name      | rank | total_score | mlb | nfl | nhl | nba | epl | completed
--------|----------------|------|-------------|-----|-----|-----|-----|-----|----------
2       | 口味虾         | 1    | 54.0        | 8.0 | 13.0| 12.0| 8.0 | 13.0| 2
8       | 揍魔王         | 2    | 51.5        | 7.0 | 11.0| 11.0| 9.0 | 13.5| 2
```

---

## 🔄 数据更新流程

### 1. 每周同步 (power_rank)

```python
# sync_team_yahoo_simple.py
# 更新 team_scores.power_rank
UPDATE team_scores 
SET power_rank = ?, updated_at = datetime('now')
WHERE team_id = ? AND sport = ?
```

### 2. 常规赛结束 (regular_bonus)

```python
# update_epl_bonus.py
# 更新 team_scores.regular_bonus
UPDATE team_scores 
SET regular_bonus = ?, 
    power_rank = ?,
    total_score = COALESCE(playoff_score, 0) + ?,
    updated_at = datetime('now')
WHERE team_id = ? AND sport = ?
```

### 3. 季后赛结束 (playoff_score, is_final)

```python
# update_epl_playoff.py
# 更新 team_scores.playoff_score 和 is_final
UPDATE team_scores 
SET playoff_rank = ?,
    playoff_score = ?,
    total_score = COALESCE(regular_bonus, 0) + ?,
    is_final = 1,
    updated_at = datetime('now')
WHERE team_id = ? AND sport = ?
```

### 4. 更新排行榜 (team_leaderboard)

```python
# 由各个更新脚本调用
# 重新计算所有队伍的总分和排名
def update_leaderboard(db_path):
    # 1. 从team_scores汇总各联赛分数
    # 2. 计算总分
    # 3. 排序
    # 4. 更新team_leaderboard表
```

---

## 📊 ironman.db (铁人个人赛)

### 主要表结构

#### players (选手表)
- player_id
- player_name
- created_at

#### player_scores (选手积分表)
- player_id
- league_id
- sport
- roto_score (Roto积分，根据常规赛)
- bonus_score (Bonus积分，根据季后赛)
- total_score
- is_final

**注意:** ironman的积分规则与irongroup相反：
- **Roto积分** = 常规赛排名
- **Bonus积分** = 季后赛排名

---

## 🔍 查询示例

### 查看某队伍的所有联赛积分

```sql
SELECT 
    t.team_name,
    s.sport,
    s.power_rank,
    s.regular_bonus,
    s.playoff_score,
    s.total_score,
    s.is_final
FROM team_scores s
JOIN teams t ON s.team_id = t.team_id
WHERE t.team_name = '口味虾'
ORDER BY 
    CASE s.sport
        WHEN 'MLB' THEN 1
        WHEN 'NFL' THEN 2
        WHEN 'NHL' THEN 3
        WHEN 'NBA' THEN 4
        WHEN 'EPL' THEN 5
    END;
```

### 查看某联赛的所有队伍积分

```sql
SELECT 
    t.team_name,
    s.power_rank,
    s.regular_bonus,
    s.playoff_score,
    s.total_score,
    s.is_final
FROM team_scores s
JOIN teams t ON s.team_id = t.team_id
WHERE s.sport = 'EPL'
ORDER BY s.total_score DESC;
```

### 查看排行榜

```sql
SELECT 
    rank,
    team_name,
    total_score,
    mlb_score,
    nfl_score,
    nhl_score,
    nba_score,
    epl_score,
    completed_sports
FROM team_leaderboard
ORDER BY rank;
```

---

## 🛠️ 数据库维护

### 备份

```bash
# 手动备份
cp irongroup.db irongroup.db.backup_$(date +%Y%m%d)

# 定期备份（建议）
# 每月一次，保留3个月
```

### 清理（新赛季开始）

```sql
-- 清空积分数据（保留队伍和联赛信息）
DELETE FROM team_scores;
DELETE FROM team_leaderboard;

-- 重置联赛状态
UPDATE leagues SET status = 'active';
```

### 数据验证

```sql
-- 检查EPL bonus总分（应为6.5）
SELECT SUM(regular_bonus) as total_bonus
FROM team_scores
WHERE sport = 'EPL';

-- 检查EPL playoff总分（应为108，如适用）
SELECT SUM(playoff_score) as total_playoff
FROM team_scores
WHERE sport = 'EPL' AND is_final = 1;

-- 检查每个队伍的记录数（应为5个联赛）
SELECT t.team_name, COUNT(*) as league_count
FROM teams t
LEFT JOIN team_scores s ON t.team_id = s.team_id
GROUP BY t.team_id, t.team_name
ORDER BY league_count;
```

---

## 📝 注意事项

1. **字段名称一致性**
   - irongroup使用: `regular_bonus`, `playoff_score`
   - 不是: `regular_season`, `playoff`

2. **积分范围**
   - regular_bonus: 0-3 (只有前4名)
   - playoff_score: 3-13 (全部12队)

3. **is_final标志**
   - 0 = 未完成（常规赛或季后赛进行中）
   - 1 = 已完成（该联赛全部结束）

4. **NULL处理**
   - 使用 `COALESCE(field, 0)` 处理NULL值
   - total_score = `COALESCE(regular_bonus, 0) + COALESCE(playoff_score, 0)`

---

**最后更新:** 2026-01-20  
**维护者:** QB
