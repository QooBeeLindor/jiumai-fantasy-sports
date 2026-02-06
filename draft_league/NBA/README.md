# 🏀 NBA Draft League - Overall Roto Rankings System

跨12个蛇形选秀联赛的综合Roto积分排名系统

## 📊 项目概述

九麦NBA蛇形选秀联赛是一个多层级的梦幻篮球联赛系统，包含12个联赛，采用1-3-4-4的阶梯架构：
- **一级盟**：NBA大师盟（16人）
- **二级盟**：WEST、EAST、CENTRAL（各16人）
- **三级盟**：暴扣、绝杀、摘帽、勾手（各16人）
- **四级盟**：力劈华山、旱地拔葱、鹰击长空、凌空飞渡（各16人）

NBA Draft League是一个综合性的范特西篮球数据分析系统，覆盖12个蛇形选秀联赛，包含192支队伍，提供Overall Roto排名、分盟详情、ADP分析、FA交易排行等功能。

### 核心功能

- **Overall Roto Rankings**: 跨联赛综合Roto积分排名
- **分盟排名**: 12个联赛的详细排名和数据
- **ADP排行**: 选秀轮次价值分析
- **FA排行榜**: 自由球员交易活跃度统计
- **赛程系统**: 每周对阵安排和历史记录

## 🎯 系统特点

### 1. 数据来源
- Yahoo Fantasy Basketball API
- 12个联赛实时数据同步
- 本地生成JSON数据文件

### 2. 技术架构
- **后端**: Python 3 + Flask
- **前端**: React 18 + Vite + TailwindCSS
- **数据库**: SQLite
- **部署**: Nginx + systemd

### 3. 部署信息
- **服务器**: 129.204.8.241
- **域名**: jiumaifantasy.online
- **访问路径**: `/NBA/draftleague/`
- **API端口**: 5003
- **完整URL**: http://jiumaifantasy.online/NBA/draftleague/

## 📁 项目结构

```
draft_league/NBA/
├── react-frontend/              # React前端
│   ├── src/
│   │   ├── components/         # 组件
│   │   │   └── Layout.jsx
│   │   ├── pages/              # 页面
│   │   │   ├── HomePage.jsx
│   │   │   ├── OverallRotoPage.jsx
│   │   │   ├── LeagueDetailPage.jsx
│   │   │   ├── LeagueListPage.jsx
│   │   │   ├── ADPPage.jsx
│   │   │   ├── FARankingsPage.jsx
│   │   │   └── SchedulePage.jsx
│   │   ├── services/           # API服务
│   │   │   └── api.js
│   │   └── App.jsx
│   ├── public/                 # 静态资源
│   │   ├── jiumai-logo.jpg
│   │   └── basketball.svg
│   ├── vite.config.js
│   ├── .env.production
│   └── package.json
│
├── complete_api_final.py       # Flask API后端
├── fetch_league_standings.py   # 数据获取脚本
├── database/
│   └── draft_league.db         # SQLite数据库
├── league_standings_map.json   # 联赛简要数据
└── league_standings_full.json  # 联赛完整数据
├── config/               # 配置文件
│   └── oauth2.json      # Yahoo API认证
```

## 🚀 部署配置

### 服务器配置
```bash
# 项目目录
/var/www/nba-app/
├── complete_api_final.py
├── league_standings_map.json
├── league_standings_full.json
├── database/draft_league.db
├── dist/                        # React构建产物
└── logs/                        # 运行日志
```

### systemd服务
```ini
# /etc/systemd/system/nba-api.service
[Unit]
Description=NBA Draft League API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/var/www/nba-app
ExecStart=/usr/bin/python3 /var/www/nba-app/complete_api_final.py
Restart=always
RestartSec=10
StandardOutput=append:/var/www/nba-app/logs/api.log
StandardError=append:/var/www/nba-app/logs/error.log

[Install]
WantedBy=multi-user.target
```

### Nginx配置
```nginx
# 前端
location /NBA/draftleague {
    alias /var/www/nba-app/dist;
    try_files $uri $uri/ /NBA/draftleague/index.html;
    index index.html;
}

# API
location /NBA/draftleague/api {
    rewrite ^/NBA/draftleague/api(.*)$ /api$1 break;
    proxy_pass http://127.0.0.1:5003;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

## 📊 API端点

### 基础API
- `GET /api/health` - 健康检查

### Overall Roto API
- `GET /api/overall_roto/rankings` - 综合排名
- `GET /api/overall_roto/team/<key>` - 队伍详情
- `GET /api/overall_roto/leagues` - 联赛列表
- `GET /api/overall_roto/stats` - 统计信息

### League Detail API
- `GET /api/league_standings` - 所有联赛排名
- `GET /api/league/<id>/detail` - 联赛详情页

### ADP API
- `GET /api/adp/rankings` - ADP排名
- `GET /api/adp/stats` - ADP统计

### FA Rankings API
- `GET /api/fa/rankings` - FA排行榜
- `GET /api/fa/player/<id>` - 球员FA详情
- `GET /api/fa/stats` - FA统计

### Schedule API
- `GET /api/schedule/weeks` - 周次列表
- `GET /api/schedule/week/<week>` - 周赛程
- `GET /api/schedule/player/<id>` - 球员赛程
- `GET /api/schedule/stats` - 赛程统计

## 🔄 数据更新流程

### 导入选秀数据（季初一次）

```bash
python scripts/import_draft_picks.py data/draft_results_2025.xlsx
```


### 每周更新（本地操作）

1. **运行数据获取脚本**
```bash
cd G:\下载\jiumai-fantasy-sports-v2\draft_league\NBA
python fetch_league_standings.py
```

2. **上传数据文件**
使用WinSCP上传到服务器：
- `league_standings_map.json` → `/var/www/nba-app/`
- `league_standings_full.json` → `/var/www/nba-app/`

3. **验证更新**
访问网站刷新页面，数据自动生效，无需重启服务。

## 🛠️ 本地开发

### 前端开发

```bash
cd react-frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
# 访问 http://localhost:3000

# 构建生产版本
npm run build
```

### 后端开发

```bash
# 安装Python依赖
pip install Flask Flask-CORS

# 运行后端服务
python complete_api_final.py
# API运行在 http://localhost:5003
```

## 📝 维护指南

### 服务管理

```bash
# 查看服务状态
sudo systemctl status nba-api

# 重启服务
sudo systemctl restart nba-api

# 查看日志
tail -f /var/www/nba-app/logs/api.log
tail -f /var/www/nba-app/logs/error.log

# 测试API
curl http://127.0.0.1:5003/api/health
```

### 前端更新

```bash
# 本地构建
npm run build

# 上传dist目录内容到服务器
# /var/www/nba-app/dist/

# 刷新浏览器
Ctrl+Shift+R
```

## 🎨 功能特性

### Overall Roto排名
- 跨12个联赛的综合Roto积分
- 192支队伍完整排名
- 实时数据更新
- 联赛筛选功能

### 分盟详情
- 每个联赛独立排名页面
- 9项数据指标展示
- 详细队伍信息
- 历史数据追踪

### ADP分析
- 选秀轮次价值分析
- Top 250球员ADP
- 球队选秀策略对比

### FA排行榜
- 自由球员交易统计
- 各队交易活跃度
- 交易趋势分析

### 赛程系统
- 每周对阵安排
- 历史战绩查询
- 球员赛程管理

## 🔒 数据安全

- 敏感认证信息不上传GitHub
- `oauth2.json` 仅保存在本地
- 服务器不需要Yahoo API认证
- 数据通过JSON文件传输

## 📈 数据规模

- **联赛数量**: 12个
- **队伍总数**: 192支
- **球员数据**: 2000+球员
- **FA交易**: 21000+条记录
- **比赛场次**: 每周100+场

## 🌐 访问链接

- **生产环境**: http://jiumaifantasy.online/NBA/draftleague/
- **备用IP**: http://129.204.8.241/NBA/draftleague/

## 🤝 贡献

这是九麦联赛的私有项目，仅限联赛成员贡献。

## 📄 License

MIT License

## 📞 联系方式

如有问题或建议，请联系联赛管理员。

---

**最后更新**: 2026-02-05  
**版本**: 1.0.0  
**状态**: ✅ 生产环境运行中
