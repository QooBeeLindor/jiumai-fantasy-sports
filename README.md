# 🏆 九麦范特西体育数据系统 (Jiumai Fantasy Sports)

一个包含**四个独立系统**的综合性范特西体育数据平台，覆盖NBA、MLB、NFL、NHL、EPL等多个联赛。

## 🌐 在线访问

**主站**: https://jiumaifantasy.online  
**备用IP**: http://129.204.8.241

## 📊 四大系统概览

### 1. 🏀 NBA Waiver League (ELO系统)
**路径**: `/NBA/waiverleague/`  
**端口**: 5000  
**访问**: http://jiumaifantasy.online/NBA/waiverleague/

- 5个联赛，80支队伍，80名球员
- 专业ELO评分算法
- 11项数据指标平局调整
- 动态K因子计算
- 每周ELO追踪
- 算法说明（含数学公式）
- 队伍花名册查看

### 2. 🎯 铁人个人赛 (Ironman Individual)
**路径**: `/ironman/`  
**端口**: 5001  
**访问**: http://jiumaifantasy.online/ironman/

- 16名球员跨4个联赛竞争（MLB、NFL、NHL、NBA）
- 常规赛 + 季后赛积分
- 实时排名和统计
- 球员详情页面

### 3. 🏆 铁人团队赛 (Ironman Team)
**路径**: `/irongroup/`  
**端口**: 5002  
**访问**: http://jiumaifantasy.online/irongroup/

- 12支队伍跨5个联赛竞争（MLB、NFL、NHL、NBA、EPL）
- Power Ranking整合
- 进行中联赛的预期得分
- 队伍成员追踪

### 4. 🏀 NBA Draft League (蛇形选秀)
**路径**: `/NBA/draftleague/`  
**端口**: 5003  
**访问**: http://jiumaifantasy.online/NBA/draftleague/

- 12个蛇形选秀联赛，192支队伍
- Overall Roto综合排名
- 分盟详细排名
- ADP分析
- FA排行榜
- 赛程系统

## 🎯 系统对比

| 特性 | NBA Waiver | 铁人个人赛 | 铁人团队赛 | NBA Draft |
|------|-----------|-----------|-----------|-----------|
| 规模 | 80人/5联赛 | 16人/4联赛 | 12队/5联赛 | 192队/12联赛 |
| 评分 | ELO评级 | 固定规则 | 固定规则 | Roto积分 |
| 路由数 | 7 | 3 | 5 | 8 |
| 模板数 | 8 | 3 | 3 | 1 (React) |
| 数据库表 | 4 | 9 | 6 | 5 |
| 端口 | 5000 | 5001 | 5002 | 5003 |
| 技术栈 | Flask + Jinja2 | Flask + Jinja2 | Flask + Jinja2 | Flask + React |

## 🚀 快速开始

### 环境要求

```bash
Python 3.8+
Node.js 18+ (仅NBA Draft League)
pip
virtualenv (推荐)
```

### 安装步骤

```bash
# 克隆仓库
git clone https://github.com/QooBeeLindor/jiumai-fantasy-sports.git
cd jiumai-fantasy-sports

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装Python依赖
pip install -r requirements.txt

# NBA Draft League需要额外构建React前端
cd draft_league/NBA/react-frontend
npm install
npm run build
```

### 本地运行

```bash
# NBA Waiver League
cd nba_elo
python app.py  # http://localhost:5000

# 铁人个人赛
cd ironman
python ironman_app.py  # http://localhost:5001

# 铁人团队赛
cd irongroup
python irongroup_app.py  # http://localhost:5002

# NBA Draft League
cd draft_league/NBA
python complete_api_final.py  # http://localhost:5003
```

## 📁 项目结构

```
jiumai-fantasy-sports/
├── nba_elo/                    # NBA Waiver League (ELO系统)
│   ├── app.py
│   ├── calculate_elo.py
│   ├── templates/
│   └── static/
│
├── ironman/                    # 铁人个人赛
│   ├── ironman_app.py
│   ├── sync_yahoo_standings.py
│   ├── templates/
│   └── ironman.db
│
├── irongroup/                  # 铁人团队赛
│   ├── irongroup_app.py
│   ├── sync_team_yahoo_simple.py
│   ├── templates/
│   └── irongroup.db
│
├── draft_league/NBA/           # NBA Draft League
│   ├── complete_api_final.py
│   ├── fetch_league_standings.py
│   ├── react-frontend/         # React前端
│   │   ├── src/
│   │   ├── public/
│   │   └── dist/
│   ├── database/
│   │   └── draft_league.db
│   └── *.json                  # 数据文件
│
├── data/                       # 数据库schemas
├── docs/                       # 文档
├── deployment/                 # 部署配置
└── requirements.txt
```

## 🔄 数据同步

### NBA Waiver League

```bash
cd nba_elo
python calculate_elo.py  # 计算ELO评分
```

### 铁人个人赛

```bash
cd ironman
python sync_yahoo_standings.py
```

### 铁人团队赛

```bash
cd irongroup
python sync_team_yahoo_simple.py irongroup.db oauth2.json
```

### NBA Draft League

```bash
cd draft_league/NBA
python fetch_league_standings.py  # 生成JSON数据文件
# 然后上传JSON文件到服务器
```

## 🌐 部署架构

### 服务器配置

```
服务器: 129.204.8.241 (jiumaifantasy.online)
操作系统: Ubuntu 22.04 LTS
Web服务器: Nginx 1.18.0
进程管理: systemd
用户: ubuntu
```

### Nginx配置

```nginx
server {
    listen 80;
    server_name jiumaifantasy.online 129.204.8.241;
    
    # 根路径重定向
    location = / {
        return 301 /NBA/waiverleague/;
    }
    
    # NBA Waiver League
    location /NBA/waiverleague/ {
        proxy_pass http://127.0.0.1:5000/;
    }
    
    # 铁人个人赛
    location /ironman/ {
        proxy_pass http://127.0.0.1:5001;
    }
    
    # 铁人团队赛
    location /irongroup/ {
        proxy_pass http://127.0.0.1:5002;
    }
    
    # NBA Draft League - 前端
    location /NBA/draftleague {
        alias /var/www/nba-app/dist;
        try_files $uri $uri/ /NBA/draftleague/index.html;
    }
    
    # NBA Draft League - API
    location /NBA/draftleague/api {
        rewrite ^/NBA/draftleague/api(.*)$ /api$1 break;
        proxy_pass http://127.0.0.1:5003;
    }
}
```

### systemd服务

所有系统都配置为systemd服务，实现：
- 开机自启动
- 自动故障重启
- 日志管理
- 进程监控

```bash
# 服务管理
sudo systemctl status nba-waiver      # NBA Waiver League
sudo systemctl status ironman-api     # 铁人个人赛
sudo systemctl status irongroup-api   # 铁人团队赛
sudo systemctl status nba-api         # NBA Draft League
```

## 📚 文档

- **新对话指南**: `docs/FOR_NEW_CONVERSATIONS.md`
- **完整技术文档**: `docs/项目完整文档_新对话专用.md`
- **维护指南**: `docs/维护指南_v2.0.md`
- **代码参考**: `docs/CODE_REFERENCE.md`
- **项目路线图**: `JIUMAI_FANTASY_PROJECT_ROADMAP.md`
- **完成指南**: `PROJECT_COMPLETION_GUIDE_v2.1.md`

### 各系统文档

- **NBA Waiver League**: `nba_elo/README.md`
- **铁人个人赛**: `ironman/README.md`
- **铁人团队赛**: `irongroup/README.md`
- **NBA Draft League**: `draft_league/README.md`

## 🛠️ 技术栈

### 后端
- Python 3.8+
- Flask 3.0
- SQLite 3
- Yahoo Fantasy API

### 前端
- **传统系统**: HTML5 + Bootstrap 5 + jQuery
- **NBA Draft League**: React 18 + Vite + TailwindCSS

### 工具库
- Chart.js - 数据可视化
- MathJax - 数学公式渲染
- lucide-react - 图标库

### 部署
- Nginx - 反向代理
- systemd - 进程管理
- WinSCP - 文件传输

## 🔐 配置说明

### Yahoo API认证

每个系统需要 `oauth2.json` 文件用于Yahoo API访问：

```json
{
    "access_token": "...",
    "consumer_key": "...",
    "consumer_secret": "...",
    "refresh_token": "...",
    "token_time": 1234567890.123,
    "token_type": "bearer"
}
```

⚠️ **注意**: `oauth2.json` 文件不应上传到GitHub，已添加到 `.gitignore`

### 环境变量

NBA Draft League需要配置 `.env.production`:

```bash
VITE_API_URL=/NBA/draftleague
```

## 📊 数据统计

| 系统 | 联赛数 | 队伍数 | 球员数 | 数据表 |
|------|-------|--------|--------|--------|
| NBA Waiver | 5 | 80 | 80 | 4 |
| 铁人个人赛 | 4 | - | 16 | 9 |
| 铁人团队赛 | 5 | 12 | - | 6 |
| NBA Draft | 12 | 192 | 2000+ | 5 |
| **总计** | **26** | **284** | **2096+** | **24** |

## 🔧 维护

### 日常任务

- 每周更新数据（通过各系统的sync脚本）
- 监控服务器状态
- 查看错误日志

### 常用命令

```bash
# 查看所有服务状态
sudo systemctl status nba-waiver ironman-api irongroup-api nba-api

# 重启所有服务
sudo systemctl restart nba-waiver ironman-api irongroup-api nba-api

# 查看Nginx状态
sudo systemctl status nginx

# 查看日志
sudo journalctl -u nba-api -f
tail -f /var/www/nba-app/logs/api.log
```

## 🚧 开发路线图

### 短期 (1-2周)
- ✅ NBA Draft League系统上线
- ⬜ 完成EPL数据同步
- ⬜ 添加SSL/HTTPS支持

### 中期 (1-2月)
- ⬜ Web管理后台
- ⬜ 自动化数据同步 (cron jobs)
- ⬜ 数据可视化图表增强

### 长期 (3-6月)
- ⬜ 移动应用开发
- ⬜ 实时推送通知
- ⬜ 用户认证系统
- ⬜ 更多联赛支持

## 🤝 贡献

这是九麦范特西联赛的私有项目，欢迎联赛成员贡献。

### 如何贡献

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 📞 支持

如有问题或建议，请：
- 提交Issue
- 联系联赛管理员
- 查阅文档

## 🙏 致谢

感谢所有为项目做出贡献的联赛成员！

---

**Made with ❤️ for NBA Fantasy Basketball**

**最后更新**: 2026-02-05  
**维护者**: 九麦范特西联赛管理团队  
**状态**: ✅ 所有系统运行正常
