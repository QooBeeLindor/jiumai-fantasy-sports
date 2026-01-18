# 🤖 给新对话（AI助手）的项目指南

## 你好，我是新的Claude对话！

这是一个**Ironman Fantasy Sports排行榜系统**。你的任务是继续开发和维护这个项目。

---

## 📚 快速了解项目

### 项目概述
- **名称**: Ironman Fantasy Sports System（三系统架构）
- **类型**: Web应用（Flask + SQLite）
- **功能**: 
  - **NBA ELO系统**: 5个联赛（80支球队）的跨联赛ELO评分系统
  - **个人赛**: 16个玩家竞争，跨MLB/NFL/NHL/NBA四个联赛
  - **团队赛**: 12个团队竞争，跨MLB/NFL/NHL/NBA/EPL五个联赛
- **数据源**: Yahoo Fantasy API

### 技术栈
- **后端**: Python 3, Flask
- **数据库**: SQLite 3
- **前端**: HTML5, Bootstrap 5, Chart.js, MathJax
- **部署**: Nginx + Gunicorn + Supervisor
- **服务器**: Ubuntu 22.04 (腾讯云)

---

## 🗂️ 项目结构

```
ironman-fantasy-sports/
├── ironman/                        # 个人赛系统
│   ├── ironman_app.py             # Flask应用（3个路由）
│   ├── sync_yahoo_standings.py    # Yahoo数据同步脚本
│   ├── ironman.db                 # 数据库
│   ├── config.py                  # 配置文件
│   └── templates/                 # HTML模板
│       ├── ironman_index.html
│       ├── ironman_individual.html
│       └── player_detail.html
│
├── irongroup/                      # 团队赛系统
│   ├── irongroup_app.py           # Flask应用（5个路由）
│   ├── sync_team_yahoo_simple.py  # Yahoo数据同步脚本
│   ├── irongroup.db               # 数据库
│   ├── config.py                  # 配置文件
│   └── templates/                 # HTML模板
│       ├── landing.html
│       ├── leaderboard.html
│       └── team_detail.html
│
├── data/                           # 数据库Schema
│   ├── schema_ironman.sql
│   └── schema_irongroup.sql
│
├── deployment/                     # 部署配置
│   ├── nginx/default.conf
│   ├── supervisor/ironman.conf
│   └── supervisor/irongroup.conf
│
└── docs/                           # 文档
    ├── 维护指南_v2.0.md
    ├── 项目完整文档_新对话专用.md
    └── (本文档)
```

---

## 💾 数据库结构

### Ironman（个人赛）

**核心表：**
1. `players` - 16个玩家信息
2. `ironman_scores` - 每个玩家在4个联赛的积分
3. `ironman_leaderboard` - 总排行榜
4. `sport_status` - 联赛状态（进行中/已完成）
5. `sport_mappings` - 玩家的Yahoo队名映射

**积分计算：**
- 常规赛：第1名=16分...第16名=1分
- 季后赛：第1名=13分，第6和7名都是8分...第12名=3分
- 总分 = 常规赛积分 + 季后赛积分

### Irongroup（团队赛）

**核心表：**
1. `teams` - 12个团队信息
2. `team_members` - 团队成员
3. `team_scores` - 每个团队在5个联赛的积分
4. `team_leaderboard` - 总排行榜
5. `leagues` - 联赛配置

**积分计算：**
- 季后赛排名 → 积分（第1名=13分...第12名=3分）
- 常规赛可能有加分
- 总分 = 各联赛积分之和

---

## 🔄 数据流程

```
Yahoo API 
   ↓
sync脚本获取排名
   ↓
计算积分
   ↓
写入数据库
   ↓
Flask读取数据
   ↓
渲染HTML
   ↓
用户浏览器
```

### 个人赛数据同步
```bash
cd /var/www/ironman
python sync_yahoo_standings.py
```

### 团队赛数据同步
```bash
cd /var/www/irongroup
python sync_team_yahoo_simple.py irongroup.db oauth2.json
```

---

## 🛠️ 常见开发任务

### 1. 添加新功能

**示例：添加EPL到个人赛**

```python
# 1. 修改数据库schema
ALTER TABLE ironman_scores ADD COLUMN epl_points REAL DEFAULT 0;
ALTER TABLE ironman_leaderboard ADD COLUMN epl_points REAL DEFAULT 0;

# 2. 更新Flask路由
@app.route('/ironman/individual')
def ironman_individual():
    # 添加epl_points到查询
    cursor.execute('''
        SELECT ..., epl_points ...
    ''')

# 3. 更新HTML模板
<th>EPL</th>
<td>{{ player.epl_points }}</td>

# 4. 更新同步脚本
# 添加EPL联赛的同步逻辑
```

### 2. 修复Bug

**示例：修复排名计算错误**

```python
# 1. 定位问题
# 查看ironman_app.py中的排名查询SQL

# 2. 修复逻辑
cursor.execute('''
    SELECT 
        player_id,
        total_score,
        ROW_NUMBER() OVER (ORDER BY total_score DESC) as rank
    FROM ironman_scores
''')

# 3. 更新排行榜
# 运行sync脚本重新计算
```

### 3. 优化性能

```python
# 添加数据库索引
CREATE INDEX idx_player_sport ON ironman_scores(player_id, sport);
CREATE INDEX idx_leaderboard_rank ON ironman_leaderboard(rank);

# 添加查询缓存
from functools import lru_cache

@lru_cache(maxsize=1)
def get_leaderboard():
    # 缓存排行榜查询结果
    pass
```

---

## 📝 代码规范

### Python
- 遵循PEP 8
- 使用参数化查询防止SQL注入
- 函数添加docstring
- 错误处理：try-except包裹数据库操作

### SQL
```python
# ✅ 好的做法
cursor.execute('SELECT * FROM players WHERE name = ?', (player_name,))

# ❌ 坏的做法
cursor.execute(f'SELECT * FROM players WHERE name = "{player_name}"')
```

### HTML/CSS
- 语义化HTML标签
- 响应式设计（移动端友好）
- 一致的命名规范

---

## ⚠️ 已知问题和注意事项

### 1. Yahoo API限制
- **问题**: Yahoo API在中国大陆被墙
- **解决**: 使用本地同步 + 手动上传数据库

### 2. 团队赛使用nohup
- **问题**: irongroup使用nohup而非Supervisor
- **TODO**: 统一使用Supervisor管理

### 3. 积分规则特殊情况
- 季后赛第6和第7名都是8分
- 需要在代码中特殊处理：
```python
def rank_to_playoff_score(rank):
    rank_to_score = {
        1: 13, 2: 12, 3: 11, 4: 10, 5: 9,
        6: 8, 7: 8,  # 特别注意：6和7都是8分
        8: 7, 9: 6, 10: 5, 11: 4, 12: 3
    }
    return rank_to_score.get(rank, 0)
```

### 4. 数据库更新策略
- 个人赛：使用sync_yahoo_standings.py
- 团队赛：使用sync_team_yahoo_simple.py
- 两个系统独立运行，不共享数据

---

## 🚀 下一步开发优先级

### 短期（1-2周）
1. ✅ EPL数据同步（已规划）
2. 统一使用Supervisor管理进程
3. 添加SSL证书（HTTPS）

### 中期（1-2月）
4. Web管理后台
5. 自动数据同步（定时任务）
6. 数据可视化图表

### 长期（3-6月）
7. 移动端App
8. 实时数据推送
9. 用户系统（登录/权限）

---

## 🔍 调试技巧

### 查看日志
```bash
# 个人赛日志
tail -f /var/log/ironman.out.log
tail -f /var/log/ironman.err.log

# 团队赛日志
tail -f /var/log/irongroup.out.log
tail -f /var/log/irongroup.err.log
```

### 测试数据库
```bash
# 进入数据库
sqlite3 /var/www/ironman/ironman.db

# 查看表结构
.schema ironman_leaderboard

# 查询数据
SELECT * FROM ironman_leaderboard ORDER BY rank LIMIT 5;
```

### 测试Flask应用
```python
# 本地运行
cd /var/www/ironman
python ironman_app.py

# 访问
http://localhost:5000/ironman/individual
```

---

## 📖 更多文档

- **完整技术文档**: `docs/项目完整文档_新对话专用.md`
- **维护指南**: `docs/维护指南_v2.0.md`
- **数据库Schema**: `data/schema_ironman.sql`, `data/schema_irongroup.sql`

---

## 💡 开始开发

**推荐流程：**
1. ✅ **阅读本文档** - 了解项目概况
2. ✅ **查看数据库Schema** - 理解数据结构
3. ✅ **阅读代码** - 理解实现逻辑
4. ✅ **运行项目** - 本地测试
5. ✅ **开始开发** - 添加新功能或修复bug

**有问题？**
- 查看源代码中的注释
- 参考`docs/`目录下的文档
- 使用`sqlite3`工具查看数据库

---

## 🎯 你准备好了吗？

现在你已经了解了这个项目的全貌。让我们开始开发吧！

**用户想要做什么？**
- 添加新功能？
- 修复bug？
- 优化性能？
- 部署到新服务器？

**告诉我你的需求，我会帮你实现！** 🚀
