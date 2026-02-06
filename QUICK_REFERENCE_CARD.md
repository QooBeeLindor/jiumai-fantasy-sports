# 🎯 九麦范特西系统 - 快速参考卡

**服务器**: 129.204.8.241 (jiumaifantasy.online)  
**最后更新**: 2026-02-05

---

## 🌐 四大系统速览

| # | 系统名称 | 访问路径 | 端口 | 主要功能 |
|---|---------|---------|------|---------|
| 1 | NBA Waiver League | `/NBA/waiverleague/` | 5000 | ELO评分，80人/5联赛 |
| 2 | 铁人个人赛 | `/ironman/` | 5001 | 个人竞赛，16人/4联赛 |
| 3 | 铁人团队赛 | `/irongroup/` | 5002 | 团队竞赛，12队/5联赛 |
| 4 | NBA Draft League | `/NBA/draftleague/` | 5003 | 蛇形选秀，192队/12联赛 |

---

## 📂 目录结构

```
/var/www/
├── nba_elo/        → NBA Waiver League (5000)
├── ironman/        → 铁人个人赛 (5001)
├── irongroup/      → 铁人团队赛 (5002)
└── nba-app/        → NBA Draft League (5003)
```

---

## 🔄 数据更新

### NBA Waiver League
```bash
cd /var/www/nba_elo && python3 calculate_elo.py
```

### 铁人个人赛
```bash
cd /var/www/ironman && python3 sync_yahoo_standings.py
```

### 铁人团队赛
```bash
cd /var/www/irongroup && python3 sync_team_yahoo_simple.py irongroup.db oauth2.json
```

### NBA Draft League (本地→服务器)
```bash
# 本地
cd G:\...\NBA && python fetch_league_standings.py

# WinSCP上传 *.json → /var/www/nba-app/
```

---

## ⚙️ 服务管理

### 查看状态
```bash
sudo systemctl status nba-waiver      # NBA Waiver
sudo systemctl status ironman-api     # 铁人个人
sudo systemctl status irongroup-api   # 铁人团队
sudo systemctl status nba-api         # NBA Draft
```

### 重启服务
```bash
sudo systemctl restart nba-waiver
sudo systemctl restart ironman-api
sudo systemctl restart irongroup-api
sudo systemctl restart nba-api
```

### 查看日志
```bash
# NBA Draft League
tail -f /var/www/nba-app/logs/api.log
tail -f /var/www/nba-app/logs/error.log

# 其他系统
sudo journalctl -u nba-api -f
sudo journalctl -u ironman-api -f
```

---

## 🌐 Nginx管理

```bash
# 测试配置
sudo nginx -t

# 重载配置
sudo systemctl reload nginx

# 查看日志
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/jiumai_error.log
```

---

## 🔍 故障排查

### 服务不响应
```bash
# 检查端口占用
sudo netstat -tulpn | grep -E "5000|5001|5002|5003"

# 检查进程
ps aux | grep python3

# 手动测试运行
cd /var/www/nba-app && python3 complete_api_final.py
```

### API无法访问
```bash
# 测试本地连接
curl http://127.0.0.1:5003/api/health
curl http://127.0.0.1/NBA/draftleague/api/health

# 检查Nginx配置
sudo nginx -t
cat /etc/nginx/sites-available/default
```

### 数据未更新
```bash
# 检查数据文件
ls -lh /var/www/nba-app/*.json
head -20 /var/www/nba-app/league_standings_map.json

# 测试API响应
curl http://127.0.0.1:5003/api/league_standings | head -50
```

---

## 📊 技术栈对比

| 系统 | 后端 | 前端 | 数据库 | 部署 |
|------|------|------|--------|------|
| NBA Waiver | Flask | Jinja2 | SQLite | systemd |
| 铁人个人赛 | Flask | Jinja2 | SQLite | systemd |
| 铁人团队赛 | Flask | Jinja2 | SQLite | systemd |
| NBA Draft | Flask | React | SQLite | systemd |

---

## 🔗 访问链接

### 生产环境
- https://jiumaifantasy.online/NBA/waiverleague/
- https://jiumaifantasy.online/ironman/
- https://jiumaifantasy.online/irongroup/
- https://jiumaifantasy.online/NBA/draftleague/

### 备用IP
- http://129.204.8.241/NBA/waiverleague/
- http://129.204.8.241/ironman/
- http://129.204.8.241/irongroup/
- http://129.204.8.241/NBA/draftleague/

---

## 📝 系统特点

### 1. NBA Waiver League
- **核心**: ELO评分算法
- **特色**: 数学公式展示、动态K因子
- **规模**: 5联赛、80队伍

### 2. 铁人个人赛
- **核心**: 跨联赛个人积分
- **特色**: 常规赛+季后赛
- **规模**: 4联赛、16球员

### 3. 铁人团队赛
- **核心**: 团队综合竞技
- **特色**: Power Ranking、预期得分
- **规模**: 5联赛、12队伍

### 4. NBA Draft League
- **核心**: Overall Roto排名
- **特色**: 蛇形选秀分析、FA排行
- **规模**: 12联赛、192队伍

---

## 🛡️ 安全提醒

- ❌ 不要上传 `oauth2.json` 到GitHub
- ❌ 不要上传 `*.db` 数据库文件
- ❌ 不要上传真实数据 JSON 文件
- ✅ 使用 `.gitignore` 排除敏感文件
- ✅ 使用 `.example` 后缀提供配置模板

---

## 📞 紧急联系

**SSH**: `ubuntu@129.204.8.241`  
**域名**: jiumaifantasy.online  
**管理员**: 九麦联赛管理团队

---

## 🎯 常见任务速查

| 任务 | 命令 |
|------|------|
| 重启所有服务 | `sudo systemctl restart nba-waiver ironman-api irongroup-api nba-api` |
| 查看所有服务状态 | `sudo systemctl status nba-waiver ironman-api irongroup-api nba-api` |
| 测试Nginx | `sudo nginx -t` |
| 重载Nginx | `sudo systemctl reload nginx` |
| 查看端口占用 | `sudo netstat -tulpn \| grep -E "5000\|5001\|5002\|5003"` |
| 查看磁盘空间 | `df -h` |
| 查看内存使用 | `free -h` |

---

**打印此卡片备用！** 📄
