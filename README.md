# 🏆 九麦Fantasy体育联赛系统

九麦Fantasy体育联赛管理系统，目前包含NBA竞价选秀联赛ELO系统、铁人个人赛和铁人团队赛三个子系统。

## 📊 系统概况

### 已部署的系统

| 系统 | 访问地址 | 状态 |
|------|---------|------|
| NBA竞价选秀ELO | [http://129.204.8.241/NBA/waiverleague/](http://129.204.8.241/NBA/waiverleague/) | ✅ |
| 铁人个人赛 | [jiumaifantasy.online/ironman](http://jiumaifantasy.online/ironman/individual) | ✅ |
| 铁人团队赛 | [jiumaifantasy.online/irongroup](http://jiumaifantasy.online/irongroup/leaderboard) | ✅ |

### 服务器信息
- **域名:** jiumaifantasy.online
- **备用IP:** 129.204.8.241
- **服务器:** Ubuntu 24 (中国大陆)

---

## ⭐ Three Systems Overview

### 1. NBA竞价选秀联赛 ELO System (Port 5000)
- 5 leagues (80 teams, 80 players)
- Professional ELO rating algorithm
- 11-category tie adjustment
- Dynamic K-factor
- Weekly ELO tracking
- Algorithm explanation with math formulas
- Team roster viewing

### 2. 铁人个人赛 (ironman) (Port 5001)
16位选手在4个联赛中竞技：MLB、NFL、NHL、NBA

#### 积分规则
- **Roto积分**: 根据常规赛排名
- **Bonus积分**: 根据季后赛排名

### 3. 铁人团队赛 (irongroup) (Port 5002)
12支战队在5个联赛中竞技：MLB、NFL、NHL、NBA、EPL

#### 积分规则
每个联赛的总分 = **季后赛积分** + **常规赛bonus**

- **季后赛积分** (13-3分): 根据季后赛排名，全部12队
- **常规赛bonus** (3-0.5分): 根据常规赛排名，只有前4名

详见：[irongroup/README_IRONGROUP.md](./irongroup/README_IRONGROUP.md)

## 🔧 数据更新工作流

### ⚠️ 重要说明

由于Yahoo Fantasy API在中国大陆被封锁，**无法直接在服务器上同步数据**。

### 正确的数据更新流程

#### Step 1: 本地同步数据
在**本地Windows电脑**执行：

```bash
# 同步个人赛
cd /d G:\ironman
python sync_yahoo_standings.py ironman.db oauth2.json

# 同步团队赛
cd /d G:\irongroup
python sync_team_yahoo_simple.py irongroup.db oauth2.json
```

#### Step 2: 上传数据库
用**WinSCP**上传：
- `G:\ironman\ironman.db` → `/var/www/ironman/ironman.db`
- `G:\irongroup\irongroup.db` → `/var/www/irongroup/irongroup.db`

#### Step 3: 重启服务
**SSH**到服务器重启应用：

```bash
# 重启个人赛
sudo supervisorctl restart ironman

# 重启团队赛
cd /var/www/irongroup
pkill -f "gunicorn.*irongroup"
source venv/bin/activate
nohup gunicorn --bind 127.0.0.1:5002 --workers 2 irongroup_app:app > irongroup.log 2>&1 &
```

#### Step 4: 验证更新
访问网站确认数据已更新

---

## 📁 项目结构

```
jiumai-fantasy-sports/
├── README.md                    # 本文件
├── 维护指南_v2.0.md              # 详细维护文档 ⭐
│
├── irongroup/                   # 铁人团队赛
│   ├── README.md                # irongroup说明
│   ├── sync_team_yahoo_simple.py
│   ├── update_epl_bonus.py
│   └── (其他更新脚本)
│
├── ironman/                     # 铁人个人赛
│   ├── sync_yahoo_standings.py
│   └── (其他脚本)
│
├── nba_elo/                     # NBA ELO系统
│   └── (相关文件)
│
└── docs/                        # 文档
    ├── database_schema.md       # 数据库结构
    └── (其他文档)
```

---

## 📖 文档索引

### 核心文档
- **[维护指南_v2.0.md](./维护指南_v2.0.md)** ⭐ - 完整的系统维护指南
- **[irongroup/README.md](./irongroup/README.md)** - 团队赛详细说明
- **[docs/database_schema.md](./docs/database_schema.md)** - 数据库结构说明

### 开发文档
- **项目路线图**: 参见下方"项目进度"章节

---

## 🚀 快速开始

### 新用户
1. 阅读 [维护指南_v2.0.md](./维护指南_v2.0.md)
2. 了解数据更新流程（见上方）
3. 查看对应子系统的README

### 每周维护
1. 本地运行数据同步脚本
2. 上传数据库到服务器
3. 重启服务

**详细步骤:** [维护指南_v2.0.md](./维护指南_v2.0.md)

---

## 📅 项目进度

### ✅ 已完成

#### 系统部署
- [x] NBA竞价选秀ELO系统
- [x] 铁人个人赛系统
- [x] 铁人团队赛系统
- [x] 域名和SSL配置

#### 数据同步
- [x] Yahoo API OAuth认证
- [x] NHL/NBA数据自动同步（本地）
- [x] 数据库上传流程

#### 团队赛功能 (irongroup)
- [x] EPL常规赛bonus更新工具 (2026-01-20)
- [x] 自适应积分显示逻辑
- [x] 团队详情页面

### 🔄 进行中

#### 团队赛 (irongroup)
- [ ] EPL季后赛积分更新（等待EPL季后赛开始）
- [ ] NHL常规赛bonus更新（等待常规赛结束）
- [ ] NBA常规赛bonus更新（等待常规赛结束）

### ⏭ 待处理

#### 短期（本赛季）
- [ ] 其他联赛季后赛更新工具
  - [ ] NHL季后赛积分
  - [ ] NBA季后赛积分
  - [ ] NFL季后赛积分（如适用）

#### 中期（1-2个月）
- [ ] 创建通用联赛更新工具
- [ ] EPL数据同步（Fantrax API）
- [ ] Web管理后台（数据更新界面）

#### 长期（3-6个月）
- [ ] 迁移到海外服务器（解决Yahoo API访问问题）
- [ ] 自动化数据同步
- [ ] 数据可视化（趋势图、对比图）
- [ ] 监控和告警系统

---

## 💾 技术栈

### 后端
- Python 3.x
- Flask
- SQLite
- Yahoo Fantasy API
- Fantrax API (EPL)

### 前端
- HTML5 / CSS3
- JavaScript (Vanilla)
- Responsive Design

### 部署
- Nginx
- Gunicorn
- Supervisor
- Ubuntu 24

---

## 🛠️ 常见问题

### Q: 为什么不能直接在服务器上同步数据？
A: Yahoo Fantasy API在中国大陆被封锁（自2021年11月）。必须在本地同步后上传数据库。

### Q: 每周需要做什么维护？
A: 在本地运行同步脚本 → 上传数据库 → 重启服务。总计约10分钟。

### Q: 常规赛/季后赛结束时需要做什么？
A: 运行相应的bonus或playoff更新脚本，然后上传数据库。

### Q: 下赛季需要修改代码吗？
A: 不需要。代码是自适应的，只需运行相应的数据更新脚本即可。

更多问题见：[维护指南_v2.0.md](./维护指南_v2.0.md)

---

## 📞 支持

遇到问题请：
1. 查看 [维护指南_v2.0.md](./维护指南_v2.0.md) 的故障排查章节
2. 检查服务器日志
3. 参考对应子系统的README

---

## 📝 更新日志

### 2026-01-20
- ✅ 修复EPL显示问题（团队赛）
- ✅ 创建EPL常规赛bonus更新工具
- ✅ 优化积分显示逻辑（自适应）
- ✅ 更新文档和维护指南

### 2026-01-13
- ✅ 更新维护指南v2.0
- ✅ 确认Yahoo API访问问题
- ✅ 建立本地同步工作流

---

## 📄 许可证

本项目仅供内部使用。

---

**维护者:** QB 
**最后更新:** 2026-01-20
