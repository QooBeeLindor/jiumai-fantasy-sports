# 📋 GitHub仓库更新指南

本文档说明如何将NBA Draft League系统添加到GitHub仓库，并更新所有文档。

## 🎯 更新目标

1. 添加NBA Draft League子项目
2. 更新主README，修正端口和路径信息
3. 添加部署总结文档
4. 保持项目结构清晰

## 📂 需要添加的文件

### 1. NBA Draft League子项目文件

```
draft_league/
└── NBA/
    ├── README.md                       ← 子项目说明
    ├── complete_api_final.py          ← Flask后端
    ├── fetch_league_standings.py      ← 数据获取脚本
    ├── requirements.txt               ← Python依赖
    ├── database/
    │   └── .gitkeep                   ← 保留目录（不上传db文件）
    ├── react-frontend/
    │   ├── src/
    │   │   ├── components/
    │   │   ├── pages/
    │   │   ├── services/
    │   │   └── App.jsx
    │   ├── public/
    │   │   ├── jiumai-logo.jpg
    │   │   └── basketball.svg
    │   ├── vite.config.js
    │   ├── package.json
    │   ├── .env.development
    │   └── .env.production.example    ← 示例文件
    └── .gitignore                      ← 忽略规则
```

### 2. 根目录文档更新

```
jiumai-fantasy-sports/
├── README.md                           ← 更新：添加第4个系统
├── DEPLOYMENT_SUMMARY.md               ← 新增：完整部署总结
├── .gitignore                          ← 更新：添加新的忽略规则
└── docs/
    └── NBA_DRAFT_LEAGUE_DEPLOYMENT.md  ← 新增：详细部署文档
```

## 📝 需要更新的内容

### 1. 更新主README.md

**修改点**：
- ✅ 标题改为"四大系统"（原来是三个）
- ✅ 添加NBA Draft League系统介绍
- ✅ 修正端口信息：
  - NBA Waiver League: 5000 ✅
  - 铁人个人赛: 5001 ✅
  - 铁人团队赛: 5002 ✅
  - NBA Draft League: 5003 ✅（新增）
- ✅ 修正访问路径：
  - NBA Waiver League: `/NBA/waiverleague/` ✅（原来README写的是根路径）
  - 铁人个人赛: `/ironman/` ✅
  - 铁人团队赛: `/irongroup/` ✅
  - NBA Draft League: `/NBA/draftleague/` ✅（新增）
- ✅ 更新系统对比表
- ✅ 更新Nginx配置示例
- ✅ 更新项目结构

### 2. 创建 .env.production.example

```bash
# 生产环境配置示例
# 复制此文件为 .env.production 并修改为实际值

VITE_API_URL=/NBA/draftleague
```

### 3. 更新 .gitignore

```gitignore
# 现有规则保持不变...

# NBA Draft League特定忽略
draft_league/NBA/database/*.db
draft_league/NBA/oauth2.json
draft_league/NBA/*.json
draft_league/NBA/react-frontend/dist/
draft_league/NBA/react-frontend/node_modules/
draft_league/NBA/react-frontend/.env.production
draft_league/NBA/react-frontend/.env.local
```

## 🔧 Git操作步骤

### 步骤1: 准备本地文件

```bash
# 进入项目根目录
cd G:\下载\jiumai-fantasy-sports-v2

# 创建draft_league目录（如果不存在）
mkdir -p draft_league

# 复制NBA Draft League项目（排除敏感文件）
# 注意：不要复制以下文件：
# - database/*.db
# - oauth2.json
# - *.json (数据文件)
# - react-frontend/dist/
# - react-frontend/node_modules/
```

### 步骤2: 添加新文件到Git

```bash
# 查看当前状态
git status

# 添加新文件
git add draft_league/
git add README.md
git add DEPLOYMENT_SUMMARY.md
git add .gitignore

# 查看将要提交的内容
git status
```

### 步骤3: 提交更改

```bash
git commit -m "feat: 添加NBA Draft League系统

- 新增第4个系统：NBA Draft League (端口5003)
- 更新主README，修正所有系统的端口和路径信息
- 添加完整部署总结文档
- 更新.gitignore规则
- 添加React前端和Flask后端代码

系统功能：
- 12个蛇形选秀联赛，192支队伍
- Overall Roto综合排名
- 分盟详细排名
- ADP分析
- FA排行榜
- 赛程系统

技术栈：
- 后端: Python + Flask
- 前端: React + Vite + TailwindCSS
- 部署: Nginx + systemd
"
```

### 步骤4: 推送到GitHub

```bash
# 推送到远程仓库
git push origin main

# 如果是第一次推送新分支
git push -u origin main
```

## ✅ 提交前检查清单

### 代码和配置
- [ ] `complete_api_final.py` 已添加
- [ ] `fetch_league_standings.py` 已添加
- [ ] `requirements.txt` 已添加
- [ ] React前端源代码已添加
- [ ] `vite.config.js` base路径正确
- [ ] `App.jsx` basename正确
- [ ] `.env.production.example` 已创建

### 文档
- [ ] `draft_league/NBA/README.md` 已创建
- [ ] 主`README.md` 已更新
- [ ] `DEPLOYMENT_SUMMARY.md` 已添加
- [ ] 端口信息全部修正
- [ ] 路径信息全部修正

### Git配置
- [ ] `.gitignore` 已更新
- [ ] 敏感文件已排除（oauth2.json, *.db, *.json数据文件）
- [ ] node_modules 已排除
- [ ] dist 目录已排除

### 不应上传的文件
- ❌ `database/draft_league.db`
- ❌ `oauth2.json`
- ❌ `league_standings_map.json`
- ❌ `league_standings_full.json`
- ❌ `react-frontend/dist/`
- ❌ `react-frontend/node_modules/`
- ❌ `react-frontend/.env.production`

## 📋 文件清单

### 应该上传的文件

```
draft_league/NBA/
├── README.md                           ✅
├── complete_api_final.py              ✅
├── fetch_league_standings.py          ✅
├── requirements.txt                   ✅
├── database/
│   └── .gitkeep                       ✅
├── react-frontend/
│   ├── src/                           ✅ (所有源代码)
│   ├── public/                        ✅ (图片资源)
│   ├── vite.config.js                 ✅
│   ├── package.json                   ✅
│   ├── index.html                     ✅
│   ├── .env.development               ✅
│   └── .env.production.example        ✅
└── .gitignore                          ✅
```

## 🔍 验证步骤

### 1. 本地验证

```bash
# 检查.gitignore是否生效
git status

# 确认以下文件未被追踪：
# - database/*.db
# - oauth2.json
# - *.json (数据文件)
# - react-frontend/dist/
# - react-frontend/node_modules/
```

### 2. GitHub验证

推送后在GitHub上检查：
- [ ] README显示正确，包含4个系统
- [ ] draft_league目录结构完整
- [ ] 敏感文件未被上传
- [ ] 文档渲染正常

### 3. 克隆测试

```bash
# 在其他目录克隆仓库测试
cd ~/test
git clone https://github.com/QooBeeLindor/jiumai-fantasy-sports.git
cd jiumai-fantasy-sports

# 检查结构
ls -la draft_league/NBA/

# 尝试运行
cd draft_league/NBA/react-frontend
npm install
npm run build
```

## 📚 相关文档链接

部署完成后，更新以下文档的链接：

1. **主README** → 链接到各子项目README
2. **DEPLOYMENT_SUMMARY** → 作为部署参考
3. **各子项目README** → 互相引用

## 🎯 下一步

GitHub更新完成后：

1. 在README中添加徽章（可选）
   ```markdown
   ![Status](https://img.shields.io/badge/status-active-success)
   ![Python](https://img.shields.io/badge/python-3.8+-blue)
   ![React](https://img.shields.io/badge/react-18-blue)
   ```

2. 创建Release标签
   ```bash
   git tag -a v2.0.0 -m "Release v2.0.0: 添加NBA Draft League系统"
   git push origin v2.0.0
   ```

3. 更新项目Wiki（如果有）

4. 通知团队成员

## ⚠️ 注意事项

### 安全提醒
- ✅ 绝不上传 `oauth2.json` 文件
- ✅ 绝不上传数据库文件 (*.db)
- ✅ 绝不上传包含真实token的配置文件
- ✅ 使用 `.example` 后缀提供配置模板

### 最佳实践
- ✅ 提交信息清晰明确
- ✅ 使用语义化版本号
- ✅ 保持提交原子性
- ✅ 定期备份重要数据

## 📞 需要帮助？

如果在更新过程中遇到问题：
1. 检查 `.gitignore` 配置
2. 使用 `git status` 查看当前状态
3. 使用 `git diff` 查看更改
4. 参考本文档的检查清单

---

**文档版本**: 1.0.0  
**最后更新**: 2026-02-05  
**维护者**: 九麦联赛管理团队
