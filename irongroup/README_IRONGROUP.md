# 🏆 铁人团队赛系统 - 快速开始

## 📁 文件结构

```
G:\irongroup\                    ← 创建这个文件夹
├── irongroup_app.py            ← Flask应用
├── irongroup.db                ← 数据库（运行导入脚本后生成）
├── irongroup_database.sql      ← 数据库结构
├── import_irongroup_data.py    ← 数据导入脚本
├── 2526铁人团队赛.xlsx         ← Excel数据文件（从现有位置复制）
└── templates\                  ← HTML模板文件夹
    ├── landing.html
    ├── leaderboard.html
    └── team_detail.html
```

---

## 🚀 本地快速开始（3步）

### Step 1: 准备文件（2分钟）

1. **创建文件夹：**
   ```
   在 G:\ 下创建文件夹：irongroup
   ```

2. **复制文件到 G:\irongroup\：**
   - 从Claude下载的所有文件
   - 从项目文件夹复制 `2526铁人团队赛.xlsx`

3. **创建templates子文件夹：**
   ```
   在 G:\irongroup\ 下创建文件夹：templates
   ```
   然后把3个HTML文件放进去

---

### Step 2: 导入数据（1分钟）

```bash
cd /d G:\irongroup

# 运行导入脚本
python import_irongroup_data.py 2526铁人团队赛.xlsx
```

**你会看到：**
```
============================================================
铁人团队赛 - 数据导入
============================================================

创建数据库结构
✓ 数据库结构创建完成

导入团队和成员信息
✓ 槑赛德斯崩驰: 槑老师, 崩少
✓ JB章日虾.Going: 章总, Richard, 三虎
...
✓ 成功导入 12 个团队

初始化联赛信息
✅ MLB: Yahoo (League: None)
✅ NFL: Yahoo (League: 749886)
🔄 NHL: Yahoo (League: 29114)
🔄 NBA: Yahoo (League: 84043)
🔄 EPL: Fantrax (League: w8kxeqp2mcnclqc9)
✓ 联赛信息初始化完成

导入已完成项目得分（MLB和NFL）
鱼跃本垒:
  MLB: 季后赛第1名 = 13.0分 + 常规赛3.0分 = 16.0分
  NFL: 季后赛第6名 = 8.0分 + 常规赛0.0分 = 8.0分
...

更新团队排行榜
排名  球队                         总分   MLB   NFL   完成
-----------------------------------------------------------------
 1.   鱼跃本垒                      24.0  16.0   8.0  2/5
 2.   口味虾                        21.0   8.0  13.0  2/5
...

✓ 数据导入完成！
```

---

### Step 3: 启动应用（1分钟）

```bash
cd /d G:\irongroup
python irongroup_app.py
```

**打开浏览器访问：**
- 首页：http://127.0.0.1:5000/irongroup/landing
- 排行榜：http://127.0.0.1:5000/irongroup/leaderboard
- 团队详情：http://127.0.0.1:5000/irongroup/team/鱼跃本垒

---

## 🎯 验证部署

### ✅ 应该看到什么

**排行榜页面：**
```
🏆 铁人团队赛排行榜

MLB✓ 已结束   NFL✓ 已结束   NHL⚡ 进行中   NBA⚡ 进行中   EPL⚡ 进行中

排名  球队                  总分   MLB   NFL   NHL   NBA   EPL   完成
1    鱼跃本垒               24.0   16.0   8.0    -     -     -    2/5
2    口味虾                 21.0    8.0  13.0    -     -     -    2/5
3    JB章日虾.Going        19.5    7.0  12.5    -     -     -    2/5
...
```

**团队详情页：**
- 显示团队名称和排名
- 显示成员列表
- 显示MLB和NFL的详细得分
- NHL/NBA/EPL显示"暂无数据"

---

## 🔧 日常维护

### 当NHL/NBA有新数据时

**方案1：手动更新（简单）**
1. 在Excel中更新数据
2. 重新运行导入脚本

**方案2：开发同步脚本（后续）**
- 类似ironman的sync脚本
- 从Yahoo API获取数据

---

## 🌐 部署到服务器

### 服务器架构

```
http://129.204.8.241/
├── /ironman/          → 个人赛（端口5001）
└── /irongroup/        → 团队赛（端口5002）
```

### 部署步骤（详见部署文档）

1. 上传文件到服务器 `/var/www/irongroup/`
2. 创建Python虚拟环境
3. 配置Supervisor（端口5002）
4. 配置Nginx（添加/irongroup路由）
5. 重启服务

---

## 📊 数据库结构

### 5个核心表

1. **teams** - 12个团队
2. **team_members** - 团队成员关系
3. **leagues** - 5个联赛信息
4. **team_scores** - 每个团队在每个项目的得分
5. **team_leaderboard** - 团队总排行榜

---

## 🎯 当前状态

### ✅ 已完成功能

- [x] 数据库结构设计
- [x] 数据导入脚本
- [x] Flask Web应用
- [x] 团队排行榜页面
- [x] 团队详情页面
- [x] 落地页
- [x] 搜索功能
- [x] 响应式设计

### ⏳ 待开发功能

- [ ] NHL/NBA实时同步脚本
- [ ] EPL数据集成（Fantrax API）
- [ ] 数据可视化（图表）
- [ ] 历史记录查询

---

## 📞 常见问题

### Q1: 导入脚本报错找不到Excel文件

**A:** 确保Excel文件路径正确
```bash
# 检查文件是否存在
dir 2526铁人团队赛.xlsx

# 或使用完整路径
python import_irongroup_data.py "G:\ironman\2526铁人团队赛.xlsx"
```

### Q2: 浏览器访问显示404

**A:** 检查Flask是否正常运行
```bash
# 应该看到：
铁人团队赛 Web应用
访问地址:
  - http://127.0.0.1:5000/irongroup/landing
  - http://127.0.0.1:5000/irongroup/leaderboard
```

### Q3: 数据显示不对

**A:** 重新导入数据
```bash
# 删除旧数据库
del irongroup.db

# 重新导入
python import_irongroup_data.py 2526铁人团队赛.xlsx
```

### Q4: 如何更新NHL/NBA数据

**A:** 目前有两种方式
1. 手动在Excel中更新，重新运行导入脚本
2. 等待开发同步脚本（类似个人赛）

---

## 🎉 下一步

**本地测试完成后：**
1. 验证所有功能正常
2. 准备部署到服务器
3. 参考《团队赛服务器部署指南.md》

**享受你的团队赛系统！** 🚀

---

**版本：** v1.0  
**创建：** 2026-01-11  
**系统：** 铁人团队赛（MVP版本）
