# 🏆 铁人团队赛 (irongroup)

12支战队在5个联赛中争夺铁人至尊荣耀

## 📊 基本信息

- **参赛队伍:** 12支
- **比赛联赛:** MLB、NFL、NHL、NBA、EPL
- **访问地址:** [jiumaifantasy.online/irongroup](http://jiumaifantasy.online/irongroup/leaderboard)

---

## 🎯 积分规则

### 每个联赛的总分构成

**总分 = 季后赛积分 + 常规赛bonus**

#### 1. 季后赛积分 (13-3分)
- **分配依据:** 季后赛最终排名
- **分配范围:** 全部12支队伍

| 排名 | 积分 |
|:----:|:----:|
| 1 | 13 |
| 2 | 12 |
| 3 | 11 |
| 4 | 10 |
| 5 | 9 |
| 6 | 8 |
| 7 | 8 |
| 8 | 7 |
| 9 | 6 |
| 10 | 5 |
| 11 | 4 |
| 12 | 3 |

**总计:** 108分

#### 2. 常规赛bonus (3-0.5分)
- **分配依据:** 常规赛最终排名
- **分配范围:** 只有前4名获得

| 排名 | bonus积分 |
|:----:|:---------:|
| 1 | 3 |
| 2 | 2 |
| 3 | 1 |
| 4 | 0.5 |
| 5-12 | 0 |

**总计:** 6.5分

### 积分示例

假设某队伍在EPL：
- 常规赛第1名 → bonus = 3分
- 季后赛第5名 → playoff = 9分
- **EPL总分 = 3 + 9 = 12分**

---

## 📁 本地文件结构

```
G:\irongroup\                    # 本地工作目录
├── irongroup.db                 # 数据库（本地同步后上传）
├── oauth2.json                  # Yahoo OAuth认证
├── sync_team_yahoo_simple.py    # Yahoo数据同步（每周）
├── update_epl_bonus.py          # EPL常规赛bonus更新
├── update_nhl_bonus.py          # NHL常规赛bonus更新（待创建）
├── update_nba_bonus.py          # NBA常规赛bonus更新（待创建）
└── (其他更新脚本)
```

---

## 🔄 数据更新流程

### 常规维护（每周）

#### 1. 同步Yahoo数据
更新NHL和NBA的实力榜排名

```bash
cd /d G:\irongroup
python sync_team_yahoo_simple.py irongroup.db oauth2.json
```

**更新内容:**
- 更新 `power_rank` (实力榜排名)
- 网页自动显示"预期季后赛积分"

#### 2. 上传数据库
用WinSCP：
- `G:\irongroup\irongroup.db` → `/var/www/irongroup/irongroup.db`

#### 3. 重启服务
SSH执行：
```bash
cd /var/www/irongroup
pkill -f "gunicorn.*irongroup"
source venv/bin/activate
nohup gunicorn --bind 127.0.0.1:5002 --workers 2 irongroup_app:app > irongroup.log 2>&1 &
```

---

### 常规赛结束时

#### 更新常规赛bonus

以EPL为例：

```bash
cd /d G:\irongroup
python update_epl_bonus.py irongroup.db
```

**更新内容:**
- 更新 `regular_bonus` (前4名的bonus分数)
- 网页显示"常规赛bonus + 季后赛待定"

**然后:** 上传数据库 → 重启服务

#### 其他联赛

```bash
# NHL常规赛结束
python update_nhl_bonus.py irongroup.db

# NBA常规赛结束
python update_nba_bonus.py irongroup.db

# MLB常规赛结束
python update_mlb_bonus.py irongroup.db
```

---

### 季后赛结束时

#### 更新季后赛积分

```bash
cd /d G:\irongroup
python update_epl_playoff.py irongroup.db
```

**更新内容:**
- 更新 `playoff_score` (季后赛积分13-3分)
- 更新 `is_final = 1` (标记为已完成)
- 网页显示"最终积分"

**然后:** 上传数据库 → 重启服务

---

## 💾 数据库结构

### 核心表: team_scores

| 字段 | 类型 | 说明 | 何时更新 |
|------|------|------|----------|
| `team_id` | INTEGER | 团队ID | - |
| `league_id` | TEXT | 联赛ID | - |
| `sport` | TEXT | 联赛名称 (MLB/NFL/NHL/NBA/EPL) | - |
| `power_rank` | INTEGER | 实力榜排名 | 每周同步 |
| `regular_bonus` | REAL | 常规赛bonus (0-3分) | 常规赛结束 |
| `playoff_rank` | INTEGER | 季后赛排名 | 季后赛结束 |
| `playoff_score` | REAL | 季后赛积分 (3-13分) | 季后赛结束 |
| `total_score` | REAL | 总分 | 自动计算 |
| `is_final` | INTEGER | 是否完成 (0/1) | 季后赛结束 |

---

## 📊 网页显示逻辑

### 自适应显示

代码会根据数据库字段自动判断显示内容：

| 状态 | regular_bonus | playoff_score | is_final | 显示内容 |
|------|---------------|---------------|----------|----------|
| 赛季未开始 | NULL | NULL | 0 | 暂无数据 |
| 常规赛进行中 | NULL | NULL | 0 | 预期季后赛积分 (根据power_rank) |
| 常规赛结束 | 有 | NULL | 0 | bonus + "季后赛待定" |
| 季后赛进行中 | 有 | 有 | 0 | bonus + playoff (部分) |
| 赛季全部结束 | 有 | 有 | 1 | 最终积分 (bonus + playoff) |

**关键:** 代码是自适应的，不需要每赛季修改！

---

## 🛠️ 更新脚本说明

### 已有脚本

#### sync_team_yahoo_simple.py ⭐
- **用途:** 每周同步Yahoo数据
- **更新:** NHL和NBA的实力榜排名
- **频率:** 每周一次

#### update_epl_bonus.py ✅
- **用途:** EPL常规赛bonus更新
- **更新:** EPL的 `regular_bonus` 字段
- **时机:** EPL常规赛结束时（一次）

### 待创建脚本

#### update_nhl_bonus.py
- **用途:** NHL常规赛bonus更新
- **参考:** 复制 `update_epl_bonus.py` 改队伍数据

#### update_nba_bonus.py
- **用途:** NBA常规赛bonus更新

#### update_mlb_bonus.py
- **用途:** MLB常规赛bonus更新

#### update_nfl_bonus.py
- **用途:** NFL常规赛bonus更新（如适用）

#### update_*_playoff.py
- **用途:** 各联赛季后赛积分更新
- **功能:** 更新 `playoff_score` 和 `is_final`

---

## 📅 本赛季时间线 (示例)

### EPL
```
8月  ─────────── 常规赛 ───────────  5月  
      ↓                           ↓
      每周同步power_rank          运行update_epl_bonus.py
      (预期积分)                  (bonus分数)
```

### NHL / NBA
```
10月 ─────────── 常规赛 ───────────  4月  ──── 季后赛 ────  6月
      ↓                           ↓           ↓
      每周同步power_rank          bonus更新    playoff更新
      (预期积分)                  (bonus)     (最终积分)
```

### MLB
```
4月  ────────────── 常规赛 ──────────────  10月  ── 季后赛 ──  11月
      ↓                                  ↓           ↓
      每周同步power_rank                  bonus       playoff
```

### NFL
```
9月  ────── 常规赛 ──────  1月   ── 季后赛 ──  2月
      ↓                   ↓           ↓
      每周同步            bonus        playoff
```

---

## ✅ 每周维护清单

- [ ] 本地运行 `sync_team_yahoo_simple.py`
- [ ] 检查输出确认同步成功
- [ ] 用WinSCP上传 `irongroup.db`
- [ ] SSH重启irongroup服务
- [ ] 访问网站验证数据更新

**预计时间:** 10分钟

---

## 🎓 常见问题

### Q: 常规赛结束后忘记运行bonus脚本会怎样？
A: 网页会继续显示"预期季后赛积分"（根据power_rank计算），不会显示实际的bonus分数。补运行bonus脚本即可。

### Q: 可以跳过bonus直接更新playoff吗？
A: 可以，但最好按顺序更新。代码会优先显示已有的数据。

### Q: 下赛季需要修改代码吗？
A: 不需要。代码是自适应的，只需清空数据库重新开始即可。

### Q: EPL没有季后赛怎么办？
A: EPL只更新bonus，不更新playoff。`is_final` 在常规赛结束时设为1即可。

### Q: 如何创建新联赛的更新脚本？
A: 复制 `update_epl_bonus.py`，修改：
- 队伍排名数据
- 联赛名称 ('EPL' → 'NHL')
- 其他联赛特定内容

---

## 📖 参考文档

- **[根目录README](../README.md)** - 项目总览
- **[维护指南_v2.0.md](../维护指南_v2.0.md)** - 详细维护指南
- **[数据库结构](../docs/database_schema.md)** - 完整数据库说明

---

## 🔮 未来改进

### 短期
- [ ] 创建所有联赛的更新脚本
- [ ] 添加数据验证功能
- [ ] 改进错误提示

### 中期
- [ ] 创建通用更新工具（一个脚本处理所有联赛）
- [ ] Web管理界面（在网页上直接更新数据）
- [ ] 自动备份机制

### 长期
- [ ] 迁移到海外服务器（直接同步Yahoo API）
- [ ] 自动化赛季管理
- [ ] 数据可视化（趋势图、对比图）

---

**最后更新:** 2026-01-20  
**维护者:** QB
