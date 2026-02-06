# 📋 九麦范特西体育系统 - 完整部署总结

**文档日期**: 2026-02-05  
**部署状态**: ✅ 所有系统正常运行

## 🌐 系统架构总览

### 服务器信息
- **IP地址**: 129.204.8.241
- **域名**: jiumaifantasy.online
- **操作系统**: Ubuntu 22.04 LTS
- **Web服务器**: Nginx 1.18.0
- **SSH用户**: ubuntu

### 四大系统部署情况

| 系统 | 访问路径 | 端口 | 目录 | 进程管理 | 状态 |
|------|----------|------|------|----------|------|
| NBA Waiver League | `/NBA/waiverleague/` | 5000 | `/var/www/nba_elo/` | systemd | ✅ 运行中 |
| 铁人个人赛 | `/ironman/` | 5001 | `/var/www/ironman/` | systemd | ✅ 运行中 |
| 铁人团队赛 | `/irongroup/` | 5002 | `/var/www/irongroup/` | systemd | ✅ 运行中 |
| NBA Draft League | `/NBA/draftleague/` | 5003 | `/var/www/nba-app/` | systemd | ✅ 运行中 |

## 📂 服务器目录结构

```
/var/www/
├── nba_elo/                    # NBA Waiver League
│   ├── app.py
│   ├── calculate_elo.py
│   ├── templates/
│   ├── static/
│   └── nba_elo.db
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
└── nba-app/                    # NBA Draft League
    ├── complete_api_final.py
    ├── league_standings_map.json
    ├── league_standings_full.json
    ├── database/
    │   └── draft_league.db
    ├── dist/                   # React前端构建产物
    │   ├── index.html
    │   ├── assets/
    │   └── ...
    └── logs/
        ├── api.log
        └── error.log
```

## ⚙️ systemd服务配置

### 1. NBA Waiver League
**服务文件**: `/etc/systemd/system/nba-waiver.service`
```ini
[Unit]
Description=NBA Waiver League ELO System
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/var/www/nba_elo
ExecStart=/usr/bin/python3 /var/www/nba_elo/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 2. 铁人个人赛
**服务文件**: `/etc/systemd/system/ironman-api.service`
```ini
[Unit]
Description=Ironman Individual Competition API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/var/www/ironman
ExecStart=/usr/bin/python3 /var/www/ironman/ironman_app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 3. 铁人团队赛
**服务文件**: `/etc/systemd/system/irongroup-api.service`
```ini
[Unit]
Description=Ironman Team Competition API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/var/www/irongroup
ExecStart=/usr/bin/python3 /var/www/irongroup/irongroup_app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 4. NBA Draft League
**服务文件**: `/etc/systemd/system/nba-api.service`
```ini
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

## 🌐 Nginx完整配置

**配置文件**: `/etc/nginx/sites-available/default`

```nginx
server {
    listen 80;
    server_name jiumaifantasy.online 129.204.8.241;
    
    # 根路径重定向到NBA ELO
    location = / {
        return 301 /NBA/waiverleague/;
    }
    
    # NBA Waiver League (ELO系统)
    location /NBA/waiverleague/ {
        proxy_pass http://127.0.0.1:5000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Script-Name /NBA/waiverleague;
    }
    
    # 铁人个人赛
    location /ironman/ {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # 铁人团队赛
    location /irongroup/ {
        proxy_pass http://127.0.0.1:5002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    # NBA Draft League - 前端静态文件
    location /NBA/draftleague {
        alias /var/www/nba-app/dist;
        try_files $uri $uri/ /NBA/draftleague/index.html;
        index index.html;
    }
    
    # NBA Draft League - API反向代理
    location /NBA/draftleague/api {
        rewrite ^/NBA/draftleague/api(.*)$ /api$1 break;
        proxy_pass http://127.0.0.1:5003;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_http_version 1.1;
        proxy_cache_bypass $http_upgrade;
    }
    
    # 日志配置
    access_log /var/log/nginx/jiumai_access.log;
    error_log /var/log/nginx/jiumai_error.log;
}
```

## 🔄 数据更新流程

### NBA Waiver League
```bash
# 服务器端操作
cd /var/www/nba_elo
python3 calculate_elo.py
# 服务自动读取更新后的数据
```

### 铁人个人赛
```bash
# 服务器端操作
cd /var/www/ironman
python3 sync_yahoo_standings.py
# 服务自动读取更新后的数据
```

### 铁人团队赛
```bash
# 服务器端操作
cd /var/www/irongroup
python3 sync_team_yahoo_simple.py irongroup.db oauth2.json
# 服务自动读取更新后的数据
```

### NBA Draft League（特殊）
```bash
# 1. 本地电脑操作
cd G:\下载\jiumai-fantasy-sports-v2\draft_league\NBA
python fetch_league_standings.py

# 2. 用WinSCP上传JSON文件到服务器
#    - league_standings_map.json → /var/www/nba-app/
#    - league_standings_full.json → /var/www/nba-app/

# 3. 浏览器刷新页面
#    无需重启服务，API自动读取新文件
```

## 📊 端口分配

| 端口 | 系统 | 状态 |
|------|------|------|
| 80 | Nginx (HTTP) | ✅ 监听中 |
| 5000 | NBA Waiver League | ✅ 使用中 |
| 5001 | 铁人个人赛 | ✅ 使用中 |
| 5002 | 铁人团队赛 | ✅ 使用中 |
| 5003 | NBA Draft League | ✅ 使用中 |

## 🛠️ 常用维护命令

### 服务管理
```bash
# 查看所有服务状态
sudo systemctl status nba-waiver ironman-api irongroup-api nba-api

# 重启所有服务
sudo systemctl restart nba-waiver ironman-api irongroup-api nba-api

# 启用开机自启
sudo systemctl enable nba-waiver ironman-api irongroup-api nba-api

# 查看服务日志
sudo journalctl -u nba-api -f
sudo journalctl -u ironman-api -f
```

### Nginx管理
```bash
# 测试配置
sudo nginx -t

# 重载配置
sudo systemctl reload nginx

# 重启Nginx
sudo systemctl restart nginx

# 查看错误日志
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/jiumai_error.log
```

### 端口检查
```bash
# 检查所有端口占用
sudo netstat -tulpn | grep -E "5000|5001|5002|5003|80"

# 检查特定端口
sudo lsof -i :5003
```

### 进程管理
```bash
# 查看Python进程
ps aux | grep python3

# 查看资源占用
htop
```

## 🔍 故障排查

### 1. 服务无法启动
```bash
# 查看详细错误
sudo journalctl -u nba-api -n 50

# 检查文件权限
ls -la /var/www/nba-app/

# 手动测试运行
cd /var/www/nba-app
python3 complete_api_final.py
```

### 2. 网站无法访问
```bash
# 检查Nginx状态
sudo systemctl status nginx

# 检查Nginx配置
sudo nginx -t

# 查看错误日志
sudo tail -50 /var/log/nginx/error.log

# 测试端口连通性
curl http://127.0.0.1:5003/api/health
curl http://127.0.0.1/NBA/draftleague/api/health
```

### 3. 数据不更新
```bash
# 检查数据文件时间
ls -lh /var/www/nba-app/league_standings_*.json

# 检查文件内容
head -20 /var/www/nba-app/league_standings_map.json

# 检查服务是否读取新数据
tail -f /var/www/nba-app/logs/api.log
```

## 📈 性能监控

### 系统资源
```bash
# 磁盘使用
df -h

# 内存使用
free -h

# CPU使用
top

# 进程监控
htop
```

### 日志大小
```bash
# 查看日志大小
du -sh /var/log/nginx/*
du -sh /var/www/nba-app/logs/*

# 清理旧日志
sudo truncate -s 0 /var/www/nba-app/logs/api.log
```

## 🔐 安全配置

### 防火墙
```bash
# 查看防火墙状态
sudo ufw status

# 允许HTTP
sudo ufw allow 80/tcp

# 允许SSH
sudo ufw allow 22/tcp
```

### 文件权限
```bash
# 设置正确的所有者
sudo chown -R ubuntu:ubuntu /var/www/nba-app/
sudo chown -R ubuntu:ubuntu /var/www/ironman/
sudo chown -R ubuntu:ubuntu /var/www/irongroup/
sudo chown -R ubuntu:ubuntu /var/www/nba_elo/

# 设置正确的权限
chmod 755 /var/www/nba-app/
chmod 644 /var/www/nba-app/*.json
chmod 755 /var/www/nba-app/*.py
```

## 📝 部署检查清单

### 新系统部署
- [ ] 代码上传到 `/var/www/`
- [ ] 安装Python依赖
- [ ] 创建数据库
- [ ] 创建systemd服务
- [ ] 启用并启动服务
- [ ] 配置Nginx
- [ ] 测试Nginx配置
- [ ] 重载Nginx
- [ ] 测试访问
- [ ] 检查日志
- [ ] 配置开机自启

### 日常维护
- [ ] 每周更新数据
- [ ] 检查服务状态
- [ ] 查看错误日志
- [ ] 监控磁盘空间
- [ ] 备份数据库
- [ ] 清理旧日志

## 🔄 部署时间线

| 日期 | 系统 | 状态 | 备注 |
|------|------|------|------|
| 2026-01-10 | NBA Waiver League | ✅ 部署 | ELO系统上线 |
| 2026-01-10 | 铁人个人赛 | ✅ 部署 | 个人赛上线 |
| 2026-01-10 | 铁人团队赛 | ✅ 部署 | 团队赛上线 |
| 2026-02-05 | NBA Draft League | ✅ 部署 | 蛇形选秀系统上线 |

## 📞 联系信息

- **服务器**: ubuntu@129.204.8.241
- **域名**: jiumaifantasy.online
- **管理员**: 九麦联赛管理团队

## 🎯 下一步计划

- [ ] 添加SSL/HTTPS支持
- [ ] 配置自动备份
- [ ] 设置监控告警
- [ ] 优化Nginx缓存
- [ ] 添加CDN加速

---

**文档维护**: 每次部署更新后及时更新此文档  
**最后更新**: 2026-02-05  
**版本**: 1.0.0
