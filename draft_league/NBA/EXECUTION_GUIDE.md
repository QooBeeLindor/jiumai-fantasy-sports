# 🚀 项目整理执行指南

## 📋 第一阶段：清理和重构（当前阶段）

已完成的工作：
- ✅ 创建项目整理计划
- ✅ 创建新的数据库schema
- ✅ 创建联盟配置文件
- ✅ 创建.gitignore
- ✅ 创建README文档
- ✅ 创建依赖文件
- ✅ 创建数据库迁移脚本
- ✅ 创建文件清理脚本

---

## 🎯 接下来要做的事（按顺序）

### 步骤1: 文件清理（在本地执行）

**在本地项目目录中运行：**

```bash
# 将清理脚本复制到项目根目录
# 然后运行
python cleanup_project.py
```

这会：
- 删除50+个重复/备份文件
- 整理核心脚本到scripts目录
- 移动选秀数据到data目录
- 清理Python缓存

**⚠️ 重要：运行前确保已备份整个项目！**

---

### 步骤2: 数据库迁移（在本地执行）

**将以下文件复制到本地：**
- `new_schema.sql` → `database/schema.sql`
- `migrate_database.py` → `scripts/migrate_database.py`

**然后运行：**

```bash
python scripts/migrate_database.py
```

这会：
- 备份当前数据库
- 创建新数据库结构（移除ELO）
- 迁移所有有效数据
- 替换旧数据库

---

### 步骤3: 更新联盟配置（在本地执行）

**将文件复制到本地：**
- `leagues_config.yaml` → `data/leagues_config.yaml`

**然后创建初始化脚本：**

```python
# scripts/init_leagues.py
import yaml
import sqlite3

with open('data/leagues_config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

conn = sqlite3.connect('database/draft_league.db')
cursor = conn.cursor()

for league in config['leagues']:
    cursor.execute("""
        INSERT OR REPLACE INTO leagues
        (id, name, tier, yahoo_id, league_key, season, 
         teams_count, promotion_slots, relegation_slots)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        league['id'],
        league['name'],
        league['tier'],
        league['yahoo_id'],
        league['league_key'],
        config['season'],
        league['teams_count'],
        league['promotion_slots'],
        league['relegation_slots']
    ))

conn.commit()
conn.close()
print(f"✓ 已初始化 {len(config['leagues'])} 个联赛")
```

运行：
```bash
python scripts/init_leagues.py
```

---

### 步骤4: 验证清理结果

检查以下内容：

**✓ 保留的核心文件：**
```
draft_league/NBA/
├── scripts/
│   ├── scrape_draft_results.py
│   ├── calculate_adp.py
│   ├── sync_yahoo_data.py
│   ├── clean_unplayed_matches.py
│   ├── generate_fa_rankings.py
│   ├── migrate_database.py
│   └── init_leagues.py
├── data/
│   ├── draft_results_2025.xlsx
│   └── leagues_config.yaml
├── database/
│   ├── draft_league.db
│   └── schema.sql
├── web/
│   ├── index.html
│   ├── leagues.html
│   ├── matches.html
│   ├── rankings.html
│   ├── css/
│   └── js/
├── config/
│   └── oauth2.json
├── api.py
├── requirements.txt
├── .gitignore
└── README.md
```

**✗ 应该被删除的：**
- 所有带 `_old`, `_backup` 的文件
- 所有调试脚本
- ELO相关脚本
- 重复的更新脚本

---

### 步骤5: 测试核心功能

```bash
# 测试数据库
sqlite3 database/draft_league.db "SELECT name FROM leagues ORDER BY tier, name;"

# 测试API
python api.py
# 访问 http://localhost:5001

# 测试前端
# 在浏览器打开 web/index.html
```

---

## 📦 提交到GitHub

清理完成后，提交到GitHub：

```bash
cd draft_league/NBA

# 初始化Git（如果还没有）
git init

# 添加文件
git add .

# 提交
git commit -m "refactor: 移除ELO系统，重构项目结构"

# 推送到远程
git push origin main
```

---

## 🔄 第二阶段预览：选秀数据处理

下一阶段我们将：

1. **创建从Excel导入选秀数据的脚本**
   - 读取 `NBA选秀结果_完整_20260131_081152.xlsx`
   - 解析蛇形选秀顺位
   - 导入到draft_picks表
   - 计算ADP

2. **验证选秀数据完整性**
   - 检查每个联赛是否有192条记录（12轮×16人）
   - 验证球员信息准确性

3. **生成ADP排行榜**
   - 计算平均选秀顺位
   - 按位置分类
   - 导出到前端展示

---

## ❓ 遇到问题？

### 清理脚本运行失败
- 检查Python版本 >= 3.8
- 确保在项目根目录运行
- 手动删除有问题的文件

### 数据库迁移失败
- 检查是否已备份
- 确保数据库文件没有被占用
- 查看错误信息，可能需要手动处理部分数据

### 联赛配置导入失败
- 确保yaml格式正确
- 检查数据库连接
- 验证联赛ID不冲突

---

## 📞 下一步行动

**完成第一阶段后，请告诉我：**
1. 文件清理是否成功
2. 数据库迁移是否正常
3. 核心功能测试结果

**然后我们将进入第二阶段：选秀数据处理**

---

最后更新：2025-02-03
