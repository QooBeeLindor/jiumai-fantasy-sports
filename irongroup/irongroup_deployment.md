# 🚀 铁人团队赛 - 服务器部署指南

## 📋 部署概览

**目标架构：**
```
http://129.204.8.241/
├── /ironman/          → 个人赛（端口5001）✅ 已部署
└── /irongroup/        → 团队赛（端口5002）⭐ 新增
```

**预计时间：** 30分钟

---

## 📦 准备文件

### 本地文件清单

```
G:\irongroup\
├── irongroup_app.py
├── irongroup.db                 ← 导入数据后生成
├── irongroup_database.sql
├── import_irongroup_data.py
├── 2526铁人团队赛.xlsx
└── templates\
    ├── landing.html
    ├── leaderboard.html
    └── team_detail.html
```

### 配置文件（从Claude下载）

- `supervisor_irongroup.conf` - Supervisor配置
- `nginx_irongroup.conf` - Nginx配置片段

---

## 🔧 部署步骤

### Step 1: 上传文件（10分钟）

#### 1.1 使用WinSCP连接服务器

- 主机：`129.204.8.241`
- 用户：`ubuntu`

#### 1.2 上传到临时目录

**上传到 `/tmp/irongroup/`：**
- `irongroup_app.py`
- `irongroup.db`
- `templates/` 文件夹（包含3个HTML）

**上传到 `/tmp/`：**
- `supervisor_irongroup.conf`

---

### Step 2: 服务器端配置（SSH操作）

```bash
# 连接服务器
ssh ubuntu@129.204.8.241

# 创建项目目录
sudo mkdir -p /var/www/irongroup
sudo chown ubuntu:ubuntu /var/www/irongroup

# 移动文件
mv /tmp/irongroup/* /var/www/irongroup/

# 检查文件
ls -la /var/www/irongroup/
```

**应该看到：**
```
irongroup_app.py
irongroup.db
templates/
```

---

### Step 3: 创建Python环境（5分钟）

```bash
cd /var/www/irongroup

# 创建虚拟环境
python3 -m venv venv

# 激活环境
source venv/bin/activate

# 安装依赖
pip install flask
```

---

### Step 4: 配置Supervisor（5分钟）

#### 4.1 创建Supervisor配置

```bash
sudo nano /etc/supervisor/conf.d/irongroup.conf
```

**内容：**
```ini
[program:irongroup]
command=/var/www/irongroup/venv/bin/gunicorn --bind 127.0.0.1:5002 --workers 2 --timeout 60 irongroup_app:app
directory=/var/www/irongroup
user=ubuntu
autostart=true
autorestart=true
stderr_logfile=/var/log/irongroup.err.log
stdout_logfile=/var/log/irongroup.out.log
environment=PATH="/var/www/irongroup/venv/bin"
```

#### 4.2 应用配置

```bash
# 重新读取配置
sudo supervisorctl reread

# 更新
sudo supervisorctl update

# 启动服务
sudo supervisorctl start irongroup

# 检查状态
sudo supervisorctl status
```

**应该看到：**
```
nba_elo      RUNNING   pid 12345, uptime 1:23:45
ironman      RUNNING   pid 67890, uptime 0:05:23
irongroup    RUNNING   pid 11223, uptime 0:00:03  ← 新服务！
```

---

### Step 5: 配置Nginx（5分钟）

#### 5.1 备份原配置

```bash
sudo cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup.$(date +%Y%m%d%H%M%S)
```

#### 5.2 编辑Nginx配置

```bash
sudo nano /etc/nginx/sites-available/default
```

**在现有server块中添加：**

```nginx
server {
    listen 80;
    server_name 129.204.8.241;

    # NBA ELO系统（现有）
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # 铁人个人赛（现有）
    location /ironman {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # 铁人团队赛（新增）⭐
    location /irongroup {
        proxy_pass http://127.0.0.1:5002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

#### 5.3 测试并重启Nginx

```bash
# 测试配置
sudo nginx -t

# 重启nginx
sudo systemctl reload nginx
```

---

### Step 6: 验证部署（5分钟）

#### 6.1 检查服务状态

```bash
# 检查所有服务
sudo supervisorctl status

# 应该看到3个服务都在运行
nba_elo      RUNNING
ironman      RUNNING
irongroup    RUNNING
```

#### 6.2 检查端口

```bash
netstat -tuln | grep -E '5000|5001|5002'
```

**应该看到：**
```
127.0.0.1:5000  (NBA)
127.0.0.1:5001  (铁人个人赛)
127.0.0.1:5002  (铁人团队赛)
```

#### 6.3 浏览器测试

**访问这些地址：**

1. **NBA系统（应该仍正常）：**
   - `http://129.204.8.241/`

2. **铁人个人赛（应该仍正常）：**
   - `http://129.204.8.241/ironman/individual`

3. **铁人团队赛（新系统）：**
   - `http://129.204.8.241/irongroup/landing`
   - `http://129.204.8.241/irongroup/leaderboard`
   - `http://129.204.8.241/irongroup/team/鱼跃本垒`

#### 6.4 查看日志

```bash
# 查看最近的日志
sudo tail -50 /var/log/irongroup.err.log
sudo tail -50 /var/log/irongroup.out.log
```

**应该没有ERROR信息**

---

## ✅ 部署成功标志

**你应该看到：**

1. **3个服务都在运行：**
   ```
   sudo supervisorctl status
   nba_elo      RUNNING
   ironman      RUNNING
   irongroup    RUNNING
   ```

2. **3个网站都能访问：**
   - NBA: ✅ http://129.204.8.241/
   - 个人赛: ✅ http://129.204.8.241/ironman/individual
   - 团队赛: ✅ http://129.204.8.241/irongroup/leaderboard

3. **排行榜显示12个团队**

4. **MLB和NFL有数据，NHL/NBA/EPL显示"-"**

---

## 🔧 日常维护

### 查看服务状态

```bash
sudo supervisorctl status irongroup
```

### 重启服务

```bash
sudo supervisorctl restart irongroup
```

### 查看日志

```bash
# 实时查看错误日志
sudo tail -f /var/log/irongroup.err.log

# 查看最近50行
sudo tail -50 /var/log/irongroup.err.log
```

### 更新数据

**方法1：手动更新Excel并重新导入**

```bash
# 1. 上传新的irongroup.db到 /tmp/
# 2. 备份旧数据库
sudo cp /var/www/irongroup/irongroup.db /var/www/irongroup/irongroup.db.backup

# 3. 替换
sudo cp /tmp/irongroup.db /var/www/irongroup/

# 4. 重启服务
sudo supervisorctl restart irongroup
```

**方法2：开发同步脚本（后续）**

类似ironman的sync脚本，从Yahoo API获取最新数据。

### 更新代码

```bash
# 1. 上传新的irongroup_app.py到 /tmp/
# 2. 替换
sudo cp /tmp/irongroup_app.py /var/www/irongroup/

# 3. 重启服务
sudo supervisorctl restart irongroup
```

---

## ⚠️ 故障排查

### 问题1: 服务启动失败

```bash
# 查看错误日志
sudo tail -50 /var/log/irongroup.err.log

# 常见原因：
# - 数据库文件不存在
# - 端口5002被占用
# - Python环境问题
```

### 问题2: 404 Not Found

```bash
# 检查nginx配置
sudo nginx -t

# 重启nginx
sudo systemctl reload nginx

# 检查irongroup服务是否运行
sudo supervisorctl status irongroup
```

### 问题3: 数据显示不对

```bash
# 检查数据库文件
ls -la /var/www/irongroup/irongroup.db

# 检查数据
cd /var/www/irongroup
source venv/bin/activate
python3 << EOF
import sqlite3
conn = sqlite3.connect('irongroup.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM teams')
print('Teams:', cursor.fetchone()[0])
cursor.execute('SELECT COUNT(*) FROM team_scores')
print('Scores:', cursor.fetchone()[0])
conn.close()
EOF
```

### 问题4: 其他系统受影响

**回滚nginx配置：**

```bash
# 恢复备份
sudo cp /etc/nginx/sites-available/default.backup.XXXXXXXX /etc/nginx/sites-available/default

# 重启nginx
sudo systemctl reload nginx
```

---

## 🎉 部署完成！

**你现在有3个并列的系统：**

1. **NBA竞价选秀盟**
   - `http://129.204.8.241/`
   - 5个竞价联赛，80支球队

2. **铁人个人赛**
   - `http://129.204.8.241/ironman/individual`
   - 16个玩家，4个项目

3. **铁人团队赛**
   - `http://129.204.8.241/irongroup/leaderboard`
   - 12个团队，5个项目

**3个系统独立运行，互不影响！** 🚀

---

## 📊 系统架构总览

```
服务器：129.204.8.241

/var/www/
├── nba_elo/           (端口5000) → /
├── ironman/           (端口5001) → /ironman
└── irongroup/         (端口5002) → /irongroup

Nginx (端口80)
├── /             → 127.0.0.1:5000 (NBA)
├── /ironman      → 127.0.0.1:5001 (个人赛)
└── /irongroup    → 127.0.0.1:5002 (团队赛)

Supervisor管理3个服务：
├── nba_elo
├── ironman
└── irongroup
```

---

**版本：** v1.0  
**创建：** 2026-01-11  
**状态：** 生产环境部署指南
