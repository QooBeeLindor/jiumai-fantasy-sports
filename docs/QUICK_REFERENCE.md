# 🚀 NBA ELO 快速命令参考卡

**版本**: v2.1.1  
**服务器**: 129.204.8.241  
**路径**: /var/www/nba_elo

---

## 📦 一键命令集合

### 🔄 日常维护

```bash
# 查看服务状态
sudo supervisorctl status nba_elo

# 重启服务
sudo supervisorctl restart nba_elo

# 停止服务
sudo supervisorctl stop nba_elo

# 启动服务
sudo supervisorctl start nba_elo
```

### 📊 查看日志

```bash
# 实时查看正常日志
tail -f /var/log/nba_elo.out.log

# 实时查看错误日志
tail -f /var/log/nba_elo.err.log

# 查看最后50行
tail -50 /var/log/nba_elo.out.log

# 查看带时间戳的日志
tail -f /var/log/nba_elo.out.log | while read line; do echo "$(date '+%Y-%m-%d %H:%M:%S') $line"; done
```

### 💾 备份

```bash
# 快速备份数据库（带时间戳）
cd /var/www/nba_elo
cp nba_elo.db nba_elo.db.backup_$(date +%Y%m%d_%H%M%S)

# 备份整个项目
tar -czf /backup/nba_elo_$(date +%Y%m%d).tar.gz /var/www/nba_elo/

# 只备份代码（排除数据库）
tar -czf /backup/nba_elo_code_$(date +%Y%m%d).tar.gz --exclude='*.db' /var/www/nba_elo/
```

### 🔧 快速修复

```bash
# 如果服务无响应
sudo supervisorctl restart nba_elo
sudo systemctl reload nginx

# 如果端口被占用
sudo lsof -i :5000
sudo kill -9 <PID>
sudo supervisorctl start nba_elo

# 清理日志（谨慎使用）
sudo truncate -s 0 /var/log/nba_elo.out.log
sudo truncate -s 0 /var/log/nba_elo.err.log
```

---

## 📁 常用路径

```bash
# 项目根目录
cd /var/www/nba_elo

# 模板目录
cd /var/www/nba_elo/templates

# 日志目录
cd /var/log

# Nginx配置
sudo vim /etc/nginx/sites-available/default

# Supervisor配置
sudo vim /etc/supervisor/conf.d/nba_elo.conf
```

---

## 🌐 Web访问

```bash
# 生产环境
http://129.204.8.241/NBA/waiverleague/

# 主要页面
http://129.204.8.241/NBA/waiverleague/           # 首页
http://129.204.8.241/NBA/waiverleague/leagues    # 联赛对比
http://129.204.8.241/NBA/waiverleague/matches    # 比赛记录
http://129.204.8.241/NBA/waiverleague/weekly_elo # 每周ELO
http://129.204.8.241/NBA/waiverleague/algorithm  # 算法说明

# 测试连接
curl http://127.0.0.1:5000/
curl http://129.204.8.241/NBA/waiverleague/
```

---

## 🗄️ 数据库操作

```bash
# 连接数据库
cd /var/www/nba_elo
sqlite3 nba_elo.db

# 常用SQL查询（在sqlite3中执行）
.tables                           # 查看所有表
.schema players                   # 查看表结构
SELECT COUNT(*) FROM players;     # 统计玩家数
SELECT * FROM players LIMIT 5;    # 查看前5个玩家
.quit                             # 退出

# 一行命令查询
sqlite3 nba_elo.db "SELECT COUNT(*) FROM players;"
sqlite3 nba_elo.db "SELECT nickname, current_elo FROM players ORDER BY current_elo DESC LIMIT 10;"
```

---

## 📝 文件编辑

```bash
# 编辑主程序
vim /var/www/nba_elo/app.py

# 编辑模板
vim /var/www/nba_elo/templates/index.html
vim /var/www/nba_elo/templates/leagues.html

# 快速查找
grep -rn "league_name" /var/www/nba_elo/
find /var/www/nba_elo -name "*.py"
```

---

## 🔍 监控和诊断

```bash
# 查看系统资源
top                    # 实时监控
htop                   # 增强版top
df -h                  # 磁盘使用
free -h                # 内存使用

# 查看进程
ps aux | grep gunicorn
ps aux | grep app.py

# 查看端口
sudo netstat -tlnp | grep 5000
sudo lsof -i :5000

# 查看Nginx状态
sudo systemctl status nginx
sudo nginx -t          # 测试配置

# 查看Supervisor状态
sudo supervisorctl status
sudo supervisorctl tail nba_elo
```

---

## 🎯 快速部署更新

```bash
# 完整部署流程（新版本）
cd /var/www/nba_elo

# 1. 备份
cp app.py app.py.backup_$(date +%Y%m%d)
cp -r templates templates.backup_$(date +%Y%m%d)
cp nba_elo.db nba_elo.db.backup_$(date +%Y%m%d)

# 2. 上传新文件（使用scp或其他工具）
# scp app.py user@129.204.8.241:/var/www/nba_elo/
# scp templates/* user@129.204.8.241:/var/www/nba_elo/templates/

# 3. 重启服务
sudo supervisorctl restart nba_elo

# 4. 验证
curl http://127.0.0.1:5000/
tail -50 /var/log/nba_elo.err.log

# 5. 如果有问题，快速回滚
cp app.py.backup_20260124 app.py
sudo supervisorctl restart nba_elo
```

---

## 🔐 权限管理

```bash
# 检查文件权限
ls -l /var/www/nba_elo/

# 设置正确权限
sudo chown -R ubuntu:ubuntu /var/www/nba_elo/
chmod 755 /var/www/nba_elo/
chmod 644 /var/www/nba_elo/app.py
chmod 644 /var/www/nba_elo/nba_elo.db

# Nginx需要读取权限
sudo chmod 755 /var/www/nba_elo
```

---

## 🐛 故障排查

### 问题：页面500错误

```bash
# 1. 查看错误日志
tail -100 /var/log/nba_elo.err.log

# 2. 测试Python语法
cd /var/www/nba_elo
python -c "import app"

# 3. 检查数据库
sqlite3 nba_elo.db "SELECT COUNT(*) FROM players;"

# 4. 重启服务
sudo supervisorctl restart nba_elo
```

### 问题：服务无法启动

```bash
# 1. 查看Supervisor日志
sudo supervisorctl tail nba_elo stderr

# 2. 手动启动测试
cd /var/www/nba_elo
source venv/bin/activate
python app.py

# 3. 检查端口占用
sudo lsof -i :5000
```

### 问题：页面无法访问

```bash
# 1. 检查Nginx
sudo systemctl status nginx
sudo nginx -t

# 2. 测试本地访问
curl http://127.0.0.1:5000/

# 3. 检查防火墙
sudo ufw status
```

---

## 📊 性能优化

```bash
# 查看数据库大小
du -sh /var/www/nba_elo/nba_elo.db

# 优化数据库
cd /var/www/nba_elo
sqlite3 nba_elo.db "VACUUM;"

# 查看Gunicorn进程
ps aux | grep gunicorn

# 调整worker数量（编辑Supervisor配置）
sudo vim /etc/supervisor/conf.d/nba_elo.conf
# 修改: -w 2 为 -w 4（根据CPU核心数）
sudo supervisorctl restart nba_elo
```

---

## 🎨 开发调试

```bash
# 本地开发模式
cd /var/www/nba_elo
source venv/bin/activate
export FLASK_ENV=development
export FLASK_DEBUG=1
python app.py

# 测试模板渲染
python -c "from app import app; print(app.jinja_env.list_templates())"

# 检查路由
python -c "from app import app; print(app.url_map)"
```

---

## 💡 实用技巧

### 批量操作

```bash
# 批量备份
for file in app.py templates/*.html; do
    cp "$file" "$file.backup_$(date +%Y%m%d)"
done

# 批量恢复
for file in *.backup_20260124; do
    mv "$file" "${file%.backup_20260124}"
done
```

### 日志分析

```bash
# 统计错误数量
grep -c "ERROR" /var/log/nba_elo.err.log

# 查找特定错误
grep "500" /var/log/nba_elo.err.log

# 统计访问量
grep "GET /" /var/log/nba_elo.out.log | wc -l
```

### 自动化脚本

```bash
# 创建每日备份脚本
cat > /var/www/scripts/backup_nba_elo.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backup/nba_elo"
DATE=$(date +%Y%m%d)
cd /var/www/nba_elo
cp nba_elo.db $BACKUP_DIR/nba_elo_$DATE.db
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
EOF

chmod +x /var/www/scripts/backup_nba_elo.sh

# 添加到crontab（每天凌晨2点）
crontab -e
# 添加: 0 2 * * * /var/www/scripts/backup_nba_elo.sh
```

---

## 📞 紧急联系

```bash
# 如果一切都失败了...

# 1. 完全重启
sudo supervisorctl stop nba_elo
sudo systemctl restart nginx
sudo supervisorctl start nba_elo

# 2. 恢复到最近备份
cd /var/www/nba_elo
cp nba_elo.db.backup_YYYYMMDD nba_elo.db
sudo supervisorctl restart nba_elo

# 3. 查看系统日志
sudo journalctl -xe
dmesg | tail -50
```

---

## 🔗 相关链接

- **项目仓库**: https://github.com/QooBeeLindor/jiumai-fantasy-sports
- **生产环境**: http://129.204.8.241/NBA/waiverleague/
- **文档**: `/var/www/nba_elo/docs/`

---

## 📌 快捷别名（可选）

在 `~/.bashrc` 或 `~/.zshrc` 中添加：

```bash
# NBA ELO 快捷命令
alias nba='cd /var/www/nba_elo'
alias nba-restart='sudo supervisorctl restart nba_elo'
alias nba-status='sudo supervisorctl status nba_elo'
alias nba-log='tail -f /var/log/nba_elo.out.log'
alias nba-err='tail -f /var/log/nba_elo.err.log'
alias nba-backup='cd /var/www/nba_elo && cp nba_elo.db nba_elo.db.backup_$(date +%Y%m%d_%H%M%S)'
```

然后执行：
```bash
source ~/.bashrc  # 或 source ~/.zshrc
```

---

**提示**: 将此文件保存为书签或打印出来，方便日常查阅！📖

**最后更新**: 2026-01-24  
**版本**: v2.1.1
