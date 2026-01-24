# 🏀 NBA ELO Rating System

**九麦NBA竞价选秀范特西联赛 - ELO评分系统**

[![Version](https://img.shields.io/badge/version-2.1.1-blue.svg)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-3.0+-red.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](../LICENSE)

一个为九麦NBA范特西联赛设计的专业ELO评分系统，支持**5个联赛80名玩家**的实时排名和数据分析。

## 📋 目录

- [功能特性](#功能特性)
- [系统架构](#系统架构)
- [快速开始](#快速开始)
- [页面说明](#页面说明)
- [ELO算法](#elo算法)
- [部署](#部署)
- [维护](#维护)
- [更新日志](#更新日志)

---

## ✨ 功能特性

### 核心功能

- ⭐ **实时ELO排名** - 80名玩家的动态评分排行榜
- 📊 **五盟对比** - 横向对比五个联赛的整体实力
- 📈 **每周追踪** - 记录每位玩家的ELO变化历程
- 🎯 **详细统计** - 包含战绩、胜率、峰值/低谷等数据
- 🔍 **比赛记录** - 完整的历史对战数据查询
- 👥 **阵容查看** - 支持查看每个球队的详细阵容

### 技术亮点

- 🧮 **专业算法** - 基于Chess ELO改进的评分系统
- ⚖️ **平局处理** - 11-category联赛的智能平局调整
- 📱 **响应式设计** - 完美支持桌面和移动设备
- 🎨 **现代UI** - Bootstrap 5 + Chart.js 数据可视化
- 🔒 **稳定可靠** - Nginx + Gunicorn + Supervisor 生产级部署

---

## 🏗️ 系统架构

```
NBA ELO系统架构
├── 前端层
│   ├── Bootstrap 5 - UI框架
│   ├── Chart.js - 图表可视化
│   ├── MathJax - 数学公式渲染
│   └── 响应式设计
│
├── 应用层
│   ├── Flask Web框架
│   ├── Jinja2模板引擎
│   └── 7个路由/8个页面
│
├── 数据层
│   ├── SQLite数据库
│   ├── 4个核心表
│   └── Yahoo API同步
│
└── 部署层
    ├── Nginx反向代理
    ├── Gunicorn WSGI
    └── Supervisor进程管理
```

### 数据库结构

```sql
-- 玩家表
players (
  player_id, nickname, yahoo_guid,
  current_elo, initial_elo,
  games_played, wins, losses, ties
)

-- 比赛表
matches (
  match_id, week, league_id, league_name,
  team1_id, team2_id,
  team1_score, team2_score,
  team1_elo_before, team1_elo_after,
  team2_elo_before, team2_elo_after
)

-- 联赛表
leagues (
  league_id, league_name
)

-- 系统信息表
system_info (
  key, value  -- 用于记录同步时间等
)
```

---

## 🚀 快速开始

### 环境要求

- Python 3.8+
- SQLite 3
- pip

### 安装步骤

```bash
# 1. 克隆仓库
git clone https://github.com/QooBeeLindor/jiumai-fantasy-sports.git
cd jiumai-fantasy-sports/nba_elo

# 2. 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 初始化数据库
python init_db.py  # 如果有初始化脚本

# 5. 运行应用
python app.py

# 6. 访问
# 浏览器打开: http://localhost:5000
```

### 依赖包

```txt
Flask==3.0.0
gunicorn==23.0.0
yahoo-oauth==1.0
yahoo-fantasy-api==2.0
```

---

## 📄 页面说明

### 1. 首页 - ELO总排行榜 (`/`)

**功能**：
- 显示所有80名玩家的实时ELO排名
- 包含排名徽章（金/银/铜）
- 展示所属联赛、战绩、胜率等
- 支持点击玩家名查看详情
- 可查看球队阵容

**新功能（v2.1.1）**：
- ✨ 新增"所属联赛"列
- 显示每个玩家属于哪个联赛（玉衡盟、天权盟等）

**数据卡片**：
- 活跃玩家数
- 比赛场数
- 活跃联赛数
- 当前周次

### 2. 五盟对比 (`/leagues`)

**功能**：
- 横向对比5个联赛的整体数据
- 显示每个联赛的平均ELO
- 查看盟内排名
- 可视化图表对比

**五个联赛**：
1. 天枢盟
2. 天璇盟
3. 天玑盟
4. 天权盟
5. 玉衡盟

### 3. 比赛记录 (`/matches`)

**功能**：
- 查看所有历史比赛
- 按联赛和周次筛选
- 显示比分和ELO变化
- 支持平局调整显示

### 4. 每周ELO (`/weekly_elo`)

**功能**：
- 追踪每位玩家的周度ELO变化
- 表格形式展示历史数据
- 便于分析趋势

### 5. 玩家详情 (`/player/<player_id>`)

**功能**：
- 显示玩家完整统计数据
- 最近20场比赛记录
- ELO历史曲线图
- 参与的联赛信息

### 6. 球队阵容 (`/roster/<league_id>/<team_key>`)

**功能**：
- 查看球队的完整阵容
- 显示球员位置和状态
- 从静态JSON文件读取

### 7. ELO算法说明 (`/algorithm`)

**功能**：
- 详细解释ELO计算方法
- 数学公式展示（MathJax）
- K-factor动态调整说明
- 11-cat平局处理逻辑

---

## 🧮 ELO算法

### 基础公式

```
ELO变化 = K × (实际得分 - 期望得分)

期望得分 = 1 / (1 + 10^((对手ELO - 己方ELO) / 400))
```

### K-Factor 动态调整

```python
if games_played < 10:
    K = 40  # 新手期
elif games_played < 30:
    K = 32  # 成长期
else:
    K = 24  # 稳定期
```

### 11-Category 平局处理

```python
def adjust_11cat_score(score1, score2, num_categories=11):
    """
    调整11-cat联赛的比分以反映平局
    例如: 6-4-1 → 调整为 6.5-4.5 (1个平局)
    """
    total = score1 + score2
    if total < num_categories:
        num_ties = num_categories - total
        tie_points = num_ties * 0.5
        return score1 + tie_points, score2 + tie_points, num_ties
    else:
        return score1, score2, 0
```

---

## 🚢 部署

### 生产环境配置

**Nginx 配置** (`/etc/nginx/sites-available/default`)

```nginx
location /NBA/waiverleague/ {
    proxy_pass http://127.0.0.1:5000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Script-Name /NBA/waiverleague;
}
```

**Supervisor 配置** (`/etc/supervisor/conf.d/nba_elo.conf`)

```ini
[program:nba_elo]
command=/var/www/nba_elo/venv/bin/gunicorn -w 2 -b 127.0.0.1:5000 app:app
directory=/var/www/nba_elo
user=ubuntu
autostart=true
autorestart=true
stdout_logfile=/var/log/nba_elo.out.log
stderr_logfile=/var/log/nba_elo.err.log
```

### 部署步骤

```bash
# 1. 上传代码到服务器
scp -r nba_elo/ user@server:/var/www/

# 2. 配置Nginx
sudo cp deployment/nginx.conf /etc/nginx/sites-available/default
sudo nginx -t
sudo systemctl reload nginx

# 3. 配置Supervisor
sudo cp deployment/supervisor.conf /etc/supervisor/conf.d/nba_elo.conf
sudo supervisorctl reread
sudo supervisorctl update

# 4. 启动服务
sudo supervisorctl start nba_elo

# 5. 检查状态
sudo supervisorctl status nba_elo
tail -f /var/log/nba_elo.out.log
```

---

## 🔧 维护

### 日常维护

**查看服务状态**
```bash
sudo supervisorctl status nba_elo
```

**重启服务**
```bash
sudo supervisorctl restart nba_elo
```

**查看日志**
```bash
# 正常日志
tail -f /var/log/nba_elo.out.log

# 错误日志
tail -f /var/log/nba_elo.err.log
```

### 数据同步

```bash
# 从Yahoo API同步数据
cd /var/www/nba_elo
source venv/bin/activate
python sync_yahoo_data.py

# 更新阵容数据
python update_roster.py
```

### 备份

```bash
# 备份数据库
cp nba_elo.db nba_elo.db.backup_$(date +%Y%m%d)

# 备份代码
tar -czf nba_elo_backup_$(date +%Y%m%d).tar.gz /var/www/nba_elo/
```

---

## 📊 版本历史

### v2.1.1 (2026-01-24) - 当前版本

**新增**：
- ✨ 首页添加"所属联赛"列
- 显示每个玩家所属联赛（玉衡盟、天权盟等）

**修复**：
- 🐛 修复leagues页面玩家链接404错误
- 使用`url_for()`替代硬编码URL

**技术**：
- 从`matches`表获取`league_name`
- 无需修改数据库结构

### v2.1.0 (2026-01-22)

**新增**：
- 🎨 完整的Web界面重新设计
- 📄 7个功能页面
- 📊 Chart.js数据可视化
- 🧮 ELO算法详细说明

**技术**：
- 新数据库结构（4个表）
- Nginx反向代理
- Supervisor进程管理

### v2.0.0 (更早)

- 初始版本
- 基础ELO系统

[查看完整更新日志](../CHANGELOG.md)

---

## 📚 相关文档

- [项目路线图](../JIUMAI_FANTASY_PROJECT_ROADMAP.md)
- [完整指南](../PROJECT_COMPLETION_GUIDE_v2.1.md)
- [维护指南](../维护指南_v2.0.md)
- [更新日志](../CHANGELOG.md)

---

## 🤝 贡献

这是九麦范特西联赛的私有项目。欢迎联赛成员提出建议和改进。

### 如何贡献

1. Fork本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

---

## 📞 支持

- 问题反馈: [GitHub Issues](https://github.com/QooBeeLindor/jiumai-fantasy-sports/issues)
- 联系管理员: 联赛管理员

---

## 📜 许可证

本项目采用 MIT 许可证。详见 [LICENSE](../LICENSE) 文件。

---

## 🙏 致谢

- **北斗五星联赛命名**: 天枢、天璇、天玑、天权、玉衡
- **技术栈**: Flask, Bootstrap, Chart.js, MathJax
- **数据来源**: Yahoo Fantasy Sports API
- **部署**: Nginx, Gunicorn, Supervisor

---

**九麦NBA竞价选秀范特西联赛** - 让数据说话，用实力证明！🏀
