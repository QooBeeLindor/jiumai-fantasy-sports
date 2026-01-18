# 🏀 NBA ELO系统 - 完整维护指南

## 📋 目录
- [日常维护流程](#日常维护流程)
- [季后赛数据处理](#季后赛数据处理)
- [常见问题排查](#常见问题排查)
- [数据备份策略](#数据备份策略)

---

## 🔄 日常维护流程

### 每周例行更新（推荐：每周一次）

#### Step 1: 本地更新ELO数据

```bash
# 在本地电脑
cd G:\nba_elo_system

# 运行ELO更新脚本
python nba_elo.py

# 生成文件: nba_elo.db（更新后的数据库）
```

**检查点：**
- ✅ 脚本运行无错误
- ✅ 显示最新一周的比赛数据
- ✅ 球员ELO排名有变化

---

#### Step 2: 更新Roster数据（可选，每月1-2次即可）

```bash
# 在本地电脑
cd G:\nba_elo_system

# 1. 开启VPN（重要！）
# 确保能访问Yahoo.com

# 2. 运行roster获取脚本
python get_roster_data.py

# 生成文件: roster_data.json（约200KB）
```

**预期输出：**
```
============================================================
🏀 NBA Fantasy Roster 数据获取工具
============================================================

1️⃣ 连接Yahoo API...
   ✅ 连接成功

2️⃣ 从数据库获取联赛列表...
   找到 5 个联赛: ['161296', '161314', '161323', '162271', '162274']

3️⃣ 获取roster数据...
  正在获取联赛 161296 的数据...
    ✓ 郴霸湘超: 14 球员
    ✓ 极地斯芬克斯天玑: 14 球员
    ...

📊 数据统计:
   联赛数量: 5
   League 161296: 16 支球队
   ...
```

**注意事项：**
- Roster数据不需要频繁更新（球员交易、伤病变化较慢）
- 建议每2-4周更新一次
- Token可能过期，需要重新授权

---

#### Step 3: 上传文件到服务器

**使用WinSCP：**

1. **连接服务器**
   - 主机：129.204.8.241
   - 用户名：ubuntu 或 root
   - 密码：你的密码

2. **上传文件**
   - 左边窗口：`G:\nba_elo_system\`
   - 右边窗口：`/var/www/nba_elo/`
   - 拖动上传：
     - `nba_elo.db`（每周必传）
     - `roster_data.json`（可选，2-4周一次）

3. **确认上传**
   - 右边窗口查看文件时间戳是否更新

**或使用SCP命令：**
```bash
# Windows CMD
cd /d G:\nba_elo_system
scp nba_elo.db ubuntu@129.204.8.241:/var/www/nba_elo/
scp roster_data.json ubuntu@129.204.8.241:/var/www/nba_elo/
```

---

#### Step 4: 服务器端验证（可选）

```bash
# SSH登录服务器
ssh ubuntu@129.204.8.241

cd /var/www/nba_elo

# 检查文件时间戳
ls -lh nba_elo.db roster_data.json

# 验证数据库
python3 << EOF
import sqlite3
conn = sqlite3.connect('nba_elo.db')
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM matches")
print(f"总比赛数: {cursor.fetchone()[0]}")
cursor.execute("SELECT MAX(week) FROM matches")
print(f"最新周次: Week {cursor.fetchone()[0]}")
conn.close()
EOF

# 如果需要，重启服务（通常不需要，数据库文件会自动更新）
# sudo supervisorctl restart nba_elo
```

---

#### Step 5: 网站验证

访问：http://129.204.8.241

**检查点：**
- ✅ 首页ELO排名已更新
- ✅ 最新周次数据正确
- ✅ 球员详情页正常
- ✅ Roster页面显示（如果更新了roster_data.json）

---

### 快速更新流程图

```
┌─────────────────────────────────────────────┐
│  本地电脑（G:\nba_elo_system）               │
│                                             │
│  1. python nba_elo.py                      │
│     生成：nba_elo.db                        │
│                                             │
│  2. [可选，每月1-2次]                       │
│     开VPN → python get_roster_data.py      │
│     生成：roster_data.json                  │
└──────────────┬──────────────────────────────┘
               │
               │ WinSCP上传
               │ nba_elo.db
               │ roster_data.json (可选)
               ↓
┌─────────────────────────────────────────────┐
│  服务器（129.204.8.241）                     │
│  /var/www/nba_elo/                          │
│                                             │
│  → Nginx + Gunicorn 自动读取新数据           │
│  → 网站实时显示最新排名                      │
└─────────────────────────────────────────────┘
```

---

## 🏆 季后赛数据处理

### 季后赛与常规赛的区别

**常规赛特点：**
- 每周固定matchup
- 对阵表自动生成
- 数据结构稳定

**季后赛特点：**
- 单败淘汰制
- 对阵表动态变化（根据排名）
- 可能有多轮（四强、半决赛、决赛）

---

### 季后赛数据获取方式

#### 方式1：继续使用现有脚本（推荐）

**你的 `nba_elo.py` 脚本应该已经支持季后赛：**

```python
# nba_elo.py 中的matchup获取逻辑
scoreboard = league.scoreboard(week=week_num)
# Yahoo API会自动返回当前周的matchup，包括季后赛
```

**季后赛数据特征：**
- `week` 字段可能是：15, 16, 17（季后赛周）
- `matchup` 数量减少（从8场变为4场、2场、1场）
- 球队ID不变

**处理方法：**
```python
# 在 nba_elo.py 中，无需特殊处理
# Yahoo API会正确返回季后赛matchup
# 只需正常运行脚本即可

# 示例：季后赛Week 15
# matchup 1: Team A vs Team B (四强)
# matchup 2: Team C vs Team D (四强)
# matchup 3: Team E vs Team F (四强)
# matchup 4: Team G vs Team H (四强)

# Week 16（半决赛）
# matchup 1: Winner(A,B) vs Winner(C,D)
# matchup 2: Winner(E,F) vs Winner(G,H)

# Week 17（决赛）
# matchup 1: Winner(半决赛1) vs Winner(半决赛2)
```

---

#### 方式2：手动检查季后赛周数

**确认季后赛开始时间：**
```bash
cd G:\nba_elo_system

# 检查当前联赛状态
python << EOF
from yahoo_oauth import OAuth2
import yahoo_fantasy_api as yfa

sc = OAuth2(None, None, from_file='oauth2.json')
gm = yfa.Game(sc, 'nba')

# 查看联赛161296的设置
lg = gm.to_league('nba.l.161296')
settings = lg.settings()
print(f"常规赛结束周: {settings.get('end_week', 'N/A')}")
print(f"季后赛开始周: {settings.get('playoff_start_week', 'N/A')}")
print(f"当前周: {settings.get('current_week', 'N/A')}")
EOF
```

---

### 季后赛数据更新流程

**与常规赛完全相同：**

```bash
# 1. 更新ELO数据
cd G:\nba_elo_system
python nba_elo.py

# 2. 上传到服务器
# 用WinSCP上传 nba_elo.db

# 3. 网站自动显示季后赛排名
```

**网站显示差异：**
- 常规赛：显示"Week 12"
- 季后赛：显示"Week 15 (Playoffs)"
- ELO计算逻辑相同
- 排行榜继续更新

---

### 季后赛注意事项

#### 1. 联赛设置检查
```python
# 检查季后赛设置
league_settings = lg.settings()
print(f"季后赛队伍数: {league_settings.get('num_playoff_teams', 'N/A')}")
print(f"季后赛匹配规则: {league_settings.get('playoff_bracket', 'N/A')}")
```

#### 2. ELO权重调整（可选）

**如果想让季后赛权重更高：**
```python
# 在 nba_elo.py 中修改K因子
def update_elo(winner_elo, loser_elo, is_tie=False, is_playoff=False):
    K = 64 if is_playoff else 32  # 季后赛K因子加倍
    # ... 其余代码
```

#### 3. 数据标记

**建议在数据库中标记季后赛：**
```sql
-- 可以在matches表中添加标记
ALTER TABLE matches ADD COLUMN is_playoff INTEGER DEFAULT 0;

-- 或者通过week判断
-- week >= 15 即为季后赛（具体数字根据联赛设置）
```

---

### 季后赛Roster更新

**季后赛期间球员交易较少：**
- 建议季后赛开始前更新一次roster
- 季后赛期间无需频繁更新
- 决赛前可再更新一次

```bash
# 季后赛前（常规赛最后一周）
cd G:\nba_elo_system
python get_roster_data.py

# 上传到服务器
scp roster_data.json ubuntu@129.204.8.241:/var/www/nba_elo/
```

---

## 🔧 常见问题排查

### 问题1：网站显示旧数据

**原因：** 数据库文件未上传成功

**解决：**
```bash
# 检查服务器文件时间戳
ssh ubuntu@129.204.8.241
cd /var/www/nba_elo
ls -lh nba_elo.db

# 如果时间不对，重新上传
```

---

### 问题2：Roster页面显示错误

**原因：** roster_data.json 未上传或格式错误

**解决：**
```bash
# 服务器端检查
cd /var/www/nba_elo
ls -lh roster_data.json
python3 -c "import json; data=json.load(open('roster_data.json')); print(f'联赛数: {len(data[\"leagues\"])}')"

# 如果出错，重新生成并上传
```

---

### 问题3：Yahoo Token过期

**现象：** 
```
TOKEN HAS EXPIRED
```

**解决：**
```bash
cd G:\nba_elo_system

# 重新授权（运行你原来的授权脚本）
# 或者手动刷新token
python << EOF
from yahoo_oauth import OAuth2
sc = OAuth2(None, None, from_file='oauth2.json')
print(f"Token有效: {sc.token_is_valid()}")
EOF
```

---

### 问题4：VPN连接问题

**现象：** get_roster_data.py 提示 "Yahoo服务不可用"

**解决：**
1. 确认VPN已连接
2. 浏览器访问 yahoo.com 确认可访问
3. 检查VPN代理设置
4. 尝试切换VPN节点（美国/日本节点最稳定）

---

### 问题5：服务器服务停止

**检查服务状态：**
```bash
ssh ubuntu@129.204.8.241
sudo supervisorctl status nba_elo
```

**如果停止，重启：**
```bash
sudo supervisorctl restart nba_elo
sudo supervisorctl tail -f nba_elo stderr
```

---

## 💾 数据备份策略

### 本地备份

**每次更新前备份：**
```bash
cd G:\nba_elo_system

# 创建备份目录
mkdir backup_$(date +%Y%m%d)

# 备份数据库
copy nba_elo.db backup_$(date +%Y%m%d)\
copy roster_data.json backup_$(date +%Y%m%d)\
```

---

### 服务器备份

**定期备份到本地：**
```bash
# Windows CMD
cd G:\nba_elo_system\backup

# 下载服务器数据库
scp ubuntu@129.204.8.241:/var/www/nba_elo/nba_elo.db server_backup_$(date +%Y%m%d).db
```

**或设置自动备份脚本：**
```bash
# 服务器端创建备份脚本
ssh ubuntu@129.204.8.241

cat > /home/ubuntu/backup_nba_elo.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/ubuntu/nba_elo_backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
cp /var/www/nba_elo/nba_elo.db $BACKUP_DIR/nba_elo_$DATE.db
cp /var/www/nba_elo/roster_data.json $BACKUP_DIR/roster_data_$DATE.json

# 只保留最近30天的备份
find $BACKUP_DIR -name "*.db" -mtime +30 -delete
find $BACKUP_DIR -name "*.json" -mtime +30 -delete

echo "✅ 备份完成: $DATE"
EOF

chmod +x /home/ubuntu/backup_nba_elo.sh

# 设置每周日自动备份
crontab -e
# 添加：0 2 * * 0 /home/ubuntu/backup_nba_elo.sh
```

---

## 📊 性能监控

### 检查网站访问速度

```bash
# 测试响应时间
curl -w "@curl-format.txt" -o /dev/null -s http://129.204.8.241/

# 查看Nginx日志
ssh ubuntu@129.204.8.241
sudo tail -100 /var/log/nginx/access.log
```

---

### 数据库性能

```bash
# 检查数据库大小
ssh ubuntu@129.204.8.241
cd /var/www/nba_elo
du -h nba_elo.db

# 优化数据库（如果变大）
sqlite3 nba_elo.db "VACUUM;"
```

---

## 🎯 维护时间表

### 每周（必做）
- ⏰ **周一上午**
  - 更新ELO数据（运行 nba_elo.py）
  - 上传 nba_elo.db 到服务器
  - 验证网站显示最新数据

### 每月（可选）
- ⏰ **月初**
  - 更新Roster数据（运行 get_roster_data.py）
  - 上传 roster_data.json 到服务器
  - 检查Token有效性

### 季后赛期间（特别关注）
- ⏰ **每轮结束后**
  - 立即更新ELO数据
  - 发布最新排名
  - 庆祝冠军诞生！🏆

### 每季度（维护）
- ⏰ **每3个月**
  - 服务器系统更新
  - 数据库优化
  - 日志清理

---

## 🎉 赛季结束后

### 数据归档
```bash
# 本地
cd G:\nba_elo_system
mkdir season_2025_2026_final
copy nba_elo.db season_2025_2026_final\
copy roster_data.json season_2025_2026_final\

# 创建最终排名报告
python << EOF
import sqlite3
conn = sqlite3.connect('nba_elo.db')
cursor = conn.cursor()
cursor.execute("""
    SELECT nickname, current_elo, games_played, wins, losses
    FROM players
    ORDER BY current_elo DESC
    LIMIT 20
""")
print("=== 2025-2026赛季最终排名 ===")
for i, row in enumerate(cursor.fetchall(), 1):
    print(f"{i}. {row[0]}: ELO {row[1]:.1f} ({row[2]}场, {row[3]}胜{row[4]}负)")
conn.close()
EOF
```

---

### 新赛季准备

**下赛季开始前：**
1. 备份旧赛季数据
2. 清空或重置数据库
3. 重新初始化ELO分数（1500分）
4. 更新联赛ID（如果变更）
5. 重新获取Roster数据

---

## 📞 技术支持

### 快速参考

| 问题类型 | 查看日志 |
|---------|---------|
| 网站无法访问 | `sudo tail -50 /var/log/nginx/error.log` |
| Python应用错误 | `sudo tail -50 /var/log/nba_elo.err.log` |
| 服务状态 | `sudo supervisorctl status nba_elo` |

---

## ✅ 维护检查清单

**每周更新清单：**
- [ ] 本地运行 `nba_elo.py`
- [ ] 上传 `nba_elo.db` 到服务器
- [ ] 访问网站验证数据更新
- [ ] 检查首页排名变化
- [ ] 测试球员详情页
- [ ] （可选）更新Roster数据

**每月检查清单：**
- [ ] 更新Roster数据
- [ ] 检查Yahoo Token有效性
- [ ] 验证VPN连接
- [ ] 查看服务器日志
- [ ] 测试Roster页面
- [ ] 备份本地数据库

**赛季末清单：**
- [ ] 导出最终排名
- [ ] 归档完整数据
- [ ] 清理旧日志
- [ ] 准备新赛季设置

---

## 🎊 总结

你的NBA ELO系统现在完全部署成功！

**核心功能：**
✅ 实时ELO排名系统
✅ 球员详细数据展示
✅ 球队阵容查看
✅ 多联赛支持
✅ 自动化数据更新

**维护工作量：**
- 每周10分钟（更新ELO数据）
- 每月15分钟（更新Roster，可选）

**随时享受你的Fantasy NBA数据分析平台！** 🏀🎉
