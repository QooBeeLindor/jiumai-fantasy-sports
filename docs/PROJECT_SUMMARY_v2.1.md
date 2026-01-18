# 🎯 Ironman Fantasy Sports - 项目总览 v2.1

## 🏆 三系统架构

本项目包含**三个独立的范特西体育系统**：

### 1. NBA ELO系统 ⭐ (端口5000)
- **规模**: 5个联赛（北斗五星），80支球队，80位球员
- **功能**: 跨联赛ELO评分系统
- **特色**: 
  - 支持11-cat平局调整
  - 动态K因子
  - 每周ELO变化追踪
  - ELO算法详解（MathJax数学公式）
  - 球队阵容查看

### 2. Ironman个人赛 (端口5001)
- **规模**: 16个玩家
- **联赛**: MLB, NFL, NHL, NBA (4个)
- **功能**: 
  - 常规赛 + 季后赛积分
  - 个人排行榜
  - 玩家详情页

### 3. Irongroup团队赛 (端口5002)
- **规模**: 12个团队
- **联赛**: MLB, NFL, NHL, NBA, EPL (5个)
- **功能**:
  - 季后赛排名积分
  - 实力榜预期得分
  - 团队详情页

---

## 📊 系统对比

| 特性 | NBA ELO | Ironman | Irongroup |
|------|---------|---------|-----------|
| **规模** | 80球员/5联赛 | 16玩家/4联赛 | 12团队/5联赛 |
| **评分系统** | ELO评分 | 固定积分规则 | 固定积分规则 |
| **路由数** | 7个 | 3个 | 5个 |
| **HTML模板** | 8个 | 3个 | 3个 |
| **数据库表** | 4张 | 9张 | 6张 |
| **特色功能** | 算法详解,阵容查看 | DataTables | 预期得分 |
| **端口** | 5000 | 5001 | 5002 |
| **Nginx路径** | `/` | `/ironman` | `/irongroup` |

---

## 🗄️ 数据库总览

### NBA ELO (nba_elo.db) - 4张表
- `players` - 球员信息和ELO
- `matches` - 比赛记录
- `leagues` - 联赛信息（5个联赛）
- `system_info` - 更新时间

### Ironman (ironman.db) - 9张表
- `players` - 16个玩家
- `ironman_scores` - 各项目积分
- `ironman_leaderboard` - 总排行榜
- `sport_status` - 联赛状态
- `sport_mappings` - 队名映射
- `league_standings` - Yahoo原始数据
- `leagues` - 联赛配置
- `scoring_rules` - 积分规则

### Irongroup (irongroup.db) - 6张表
- `teams` - 12个团队
- `team_members` - 团队成员
- `team_scores` - 各项目积分
- `team_leaderboard` - 总排行榜
- `leagues` - 联赛配置

---

## 📁 完整项目结构

```
ironman-fantasy-sports-v2.1/
├── nba_elo/                    ⭐ NBA ELO系统
│   ├── nba_elo.py             # ELO计算（500行）
│   ├── app.py                 # Flask应用（400行）
│   ├── nba_elo.db
│   ├── config.json
│   ├── player_nicknames.json
│   └── templates/ (8个HTML)
│       ├── base.html          # 基础模板
│       ├── index.html         # ELO排行榜
│       ├── leagues.html       # 联赛对比
│       ├── matches.html       # 比赛记录
│       ├── weekly_elo.html    # 每周变化
│       ├── player.html        # 玩家详情
│       ├── roster.html        # 球队阵容
│       └── algorithm.html     # ELO算法详解
│
├── ironman/                    # 个人赛系统
│   ├── ironman_app.py         # Flask应用（200行）
│   ├── sync_yahoo_standings.py
│   ├── ironman.db
│   └── templates/ (3个HTML)
│
├── irongroup/                  # 团队赛系统
│   ├── irongroup_app.py       # Flask应用（300行）
│   ├── sync_team_yahoo_simple.py (200行)
│   ├── irongroup.db
│   └── templates/ (3个HTML)
│
├── data/                       # 数据库Schema
│   ├── schema_nba_elo.sql     ✅ 已创建
│   ├── schema_ironman.sql     ✅ 已创建
│   └── schema_irongroup.sql   ✅ 已创建
│
├── deployment/                 # 部署配置
│   ├── nginx/
│   │   └── default.conf       # 三系统路由配置
│   └── supervisor/
│       ├── nba_elo.conf
│       ├── ironman.conf
│       └── irongroup.conf
│
├── docs/                       # 文档
│   ├── FOR_NEW_CONVERSATIONS.md
│   ├── NBA_ELO_CODE_CHECKLIST.md ✅ 新增
│   ├── CODE_REFERENCE.md
│   ├── PROJECT_SUMMARY_v2.1.md  ✅ 本文档
│   ├── 维护指南_v2.0.md
│   └── 项目完整文档_新对话专用.md
│
├── README.md                   # GitHub主页
├── .gitignore
├── LICENSE
└── requirements.txt
```

---

## 🔄 数据流程

### NBA ELO系统
```
Yahoo API → nba_elo.py → 计算ELO → nba_elo.db → Flask app.py → HTML展示
```

### Ironman个人赛
```
Yahoo API → sync_yahoo_standings.py → ironman.db → ironman_app.py → HTML展示
```

### Irongroup团队赛
```
Yahoo API → sync_team_yahoo_simple.py → irongroup.db → irongroup_app.py → HTML展示
```

---

## 🚀 快速启动

### 初始化数据库
```bash
# NBA ELO
cd nba_elo
sqlite3 nba_elo.db < ../data/schema_nba_elo.sql

# Ironman
cd ../ironman
sqlite3 ironman.db < ../data/schema_ironman.sql

# Irongroup
cd ../irongroup
sqlite3 irongroup.db < ../data/schema_irongroup.sql
```

### 同步数据
```bash
# NBA ELO
cd nba_elo
python nba_elo.py  # 选择选项1

# Ironman
cd ../ironman
python sync_yahoo_standings.py

# Irongroup
cd ../irongroup
python sync_team_yahoo_simple.py irongroup.db oauth2.json
```

### 启动服务
```bash
# NBA ELO (端口5000)
cd nba_elo
python app.py

# Ironman (端口5001)
cd ../ironman
python ironman_app.py

# Irongroup (端口5002)
cd ../irongroup
python irongroup_app.py
```

---

## 📊 统计数据

### 代码量
| 系统 | Python | HTML | 总计 |
|------|--------|------|------|
| NBA ELO | ~900行 | ~1300行 | ~2200行 |
| Ironman | ~200行 | ~400行 | ~600行 |
| Irongroup | ~500行 | ~500行 | ~1000行 |
| **总计** | **~1600行** | **~2200行** | **~3800行** |

### 文件数
- Python文件: 7个
- HTML模板: 14个
- SQL Schema: 3个
- 配置文件: 5个
- 文档: 7个
- **总计**: 36个文件

---

## 🎯 给新对话的提示

### 理解顺序
1. **先读本文档** - 了解三系统架构
2. **再读FOR_NEW_CONVERSATIONS.md** - 详细了解每个系统
3. **查看CODE_REFERENCE.md** - 了解代码索引
4. **查看NBA_ELO_CODE_CHECKLIST.md** - NBA ELO代码清单

### 开发重点
- **NBA ELO系统**: 最复杂，功能最全
- **Ironman**: 标准的排行榜系统
- **Irongroup**: 团队赛，含预期得分计算

### 常见任务
- 添加新联赛 → 修改config文件
- 修改积分规则 → 修改scoring_rules表
- 添加新玩家 → 运行同步脚本
- 调整界面 → 修改HTML模板

---

## ✨ 项目亮点

### NBA ELO系统 ⭐
- 专业的ELO评分算法
- 支持11-cat平局调整
- 动态K因子（考虑比分差异）
- 完整的算法详解页面
- Chart.js可视化
- MathJax数学公式
- 球队阵容查看

### Ironman个人赛
- DataTables高级表格
- 自动刷新
- 前三名特殊颜色
- 响应式设计

### Irongroup团队赛
- 实力榜预期得分
- 纯CSS设计
- 团队成员管理
- 5个联赛支持

---

## 📝 维护建议

### 每周
- 运行数据同步脚本
- 检查服务运行状态

### 每月
- 备份数据库
- 查看日志文件
- 更新roster数据（NBA ELO）

### 赛季末
- 导出Excel报表
- 归档数据库
- 准备新赛季

---

**版本**: v2.1  
**更新日期**: 2026-01-18  
**包含系统**: NBA ELO + Ironman + Irongroup  
**状态**: 完整三系统架构 ✅
