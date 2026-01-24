# Git 提交指南 - v2.1.1 部署

## 📋 提交清单

在提交代码前，请确认：

- [ ] 代码已在生产环境测试通过
- [ ] 所有功能正常运行
- [ ] 日志无错误信息
- [ ] 文档已更新
- [ ] CHANGELOG已记录

---

## 🚀 快速提交步骤

### 第1步：检查Git状态

```bash
cd /path/to/jiumai-fantasy-sports
git status
```

### 第2步：添加修改的文件

```bash
# NBA ELO系统修改（v2.1.1）
git add nba_elo/app.py
git add nba_elo/templates/index.html
git add nba_elo/templates/leagues.html

# 新增文档
git add CHANGELOG.md
git add nba_elo/README.md

# 如果有其他修改
git add <其他文件>
```

### 第3步：提交更改

```bash
git commit -m "feat(nba-elo): 添加联赛列和修复链接 v2.1.1

✨ 新增功能:
- 首页添加'所属联赛'列，显示玩家所属联赛名称
- 使用蓝色徽章样式展示联赛（玉衡盟、天权盟等）

🐛 Bug修复:
- 修复leagues页面玩家详情链接404错误
- 将硬编码URL改为url_for()动态生成

🔧 技术改进:
- 从matches表获取league_name，无需修改数据库
- 优化查询性能，减少数据库调用

📝 文档更新:
- 新增CHANGELOG.md记录版本历史
- 创建NBA_ELO_README.md专属文档
- 更新部署和维护说明

✅ 测试:
- 生产环境验证通过
- 所有页面功能正常
- 无错误日志

版本: v2.1.1
部署: http://129.204.8.241/NBA/waiverleague/
日期: 2026-01-24"
```

### 第4步：推送到远程

```bash
git push origin main
```

### 第5步：创建版本标签（推荐）

```bash
# 创建标签
git tag -a v2.1.1 -m "版本 2.1.1 - 添加联赛列和修复链接

主要更新:
- 首页新增'所属联赛'列
- 修复leagues页面链接问题
- 优化查询性能
- 完善项目文档

部署状态: ✅ 生产环境运行中
测试状态: ✅ 全部通过"

# 推送标签
git push origin v2.1.1

# 查看所有标签
git tag -l
```

---

## 📝 提交信息规范

### 提交类型

```
feat:     新功能
fix:      Bug修复
docs:     文档更新
style:    代码格式（不影响功能）
refactor: 重构（既不是新功能也不是修复）
perf:     性能优化
test:     测试相关
chore:    构建过程或辅助工具的变动
```

### 提交格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

**示例**：

```
feat(nba-elo): 添加联赛列和修复链接 v2.1.1

新增功能:
- 首页添加所属联赛列
- 显示玩家联赛名称

Bug修复:
- 修复leagues页面链接404

测试: 生产环境验证通过
```

---

## 🏷️ 版本标签规范

### 语义化版本

```
v<major>.<minor>.<patch>

v2.1.1
│ │ │
│ │ └─ 补丁版本（Bug修复）
│ └─── 次版本（新功能，向后兼容）
└───── 主版本（重大更新，可能不兼容）
```

### 标签说明

- `v2.1.1` - 小修复，添加功能
- `v2.1.0` - 新功能，重大更新
- `v2.0.0` - 架构调整，不兼容旧版

---

## 📂 文件组织

### 本次提交涉及的文件

```
jiumai-fantasy-sports/
├── nba_elo/
│   ├── app.py                    # ✏️ 修改
│   ├── templates/
│   │   ├── index.html            # ✏️ 修改
│   │   └── leagues.html          # ✏️ 修改
│   └── README.md                 # ✨ 新增
├── CHANGELOG.md                   # ✨ 新增
└── (此文件) GIT_COMMIT_GUIDE.md # ✨ 新增
```

---

## 🔍 提交前检查

### 代码检查

```bash
# 检查Python语法
cd nba_elo
python -m py_compile app.py

# 检查HTML模板（可选）
# 使用IDE的HTML验证功能
```

### 功能测试

访问以下页面确认功能正常：

- [ ] http://129.204.8.241/NBA/waiverleague/
  - [ ] 首页显示"所属联赛"列
  - [ ] 联赛名称正确显示
  
- [ ] http://129.204.8.241/NBA/waiverleague/leagues
  - [ ] 点击"详情"链接能正常访问
  - [ ] URL格式正确（包含/NBA/waiverleague/前缀）
  
- [ ] http://129.204.8.241/NBA/waiverleague/player/xxx
  - [ ] 玩家详情页正常显示

### 日志检查

```bash
# SSH到服务器
ssh user@129.204.8.241

# 检查错误日志
tail -50 /var/log/nba_elo.err.log

# 应该没有新的错误
```

---

## 🎯 提交后验证

### 1. GitHub验证

1. 访问 https://github.com/QooBeeLindor/jiumai-fantasy-sports
2. 确认提交已显示
3. 检查文件内容是否正确
4. 验证标签是否创建

### 2. 本地验证

```bash
# 查看提交历史
git log --oneline -5

# 查看最新提交详情
git show HEAD

# 查看标签
git tag -l
git show v2.1.1
```

---

## 🚨 常见问题

### 问题1：提交后发现错误

**解决**：

```bash
# 修改最后一次提交
git add <修正的文件>
git commit --amend

# 强制推送（谨慎使用）
git push origin main --force
```

### 问题2：忘记添加某个文件

**解决**：

```bash
# 添加遗漏的文件
git add <遗漏的文件>
git commit --amend --no-edit

# 推送
git push origin main --force
```

### 问题3：标签创建错误

**解决**：

```bash
# 删除本地标签
git tag -d v2.1.1

# 删除远程标签
git push origin :refs/tags/v2.1.1

# 重新创建
git tag -a v2.1.1 -m "..."
git push origin v2.1.1
```

---

## 📊 版本历史查看

### 查看所有版本

```bash
# 查看所有标签
git tag -l

# 输出示例：
# v2.0.0
# v2.1.0
# v2.1.1
```

### 查看版本间差异

```bash
# 比较两个版本
git diff v2.1.0..v2.1.1

# 查看某个版本的详情
git show v2.1.1
```

### 切换到特定版本

```bash
# 检出特定版本（只读）
git checkout v2.1.0

# 返回最新版本
git checkout main
```

---

## 💡 最佳实践

### DO ✅

- ✅ 提交前在生产环境测试
- ✅ 使用规范的提交信息
- ✅ 每次提交只包含相关修改
- ✅ 重要版本创建标签
- ✅ 更新CHANGELOG
- ✅ 提交后验证

### DON'T ❌

- ❌ 提交未测试的代码
- ❌ 提交信息过于简单
- ❌ 一次提交混合多个不相关修改
- ❌ 直接提交到main分支（大型改动）
- ❌ 忘记更新文档
- ❌ 跳过代码审查

---

## 🔄 协作流程（如果有团队）

### 功能开发流程

```bash
# 1. 创建功能分支
git checkout -b feature/add-league-column

# 2. 开发和提交
git add .
git commit -m "feat: 添加联赛列"

# 3. 推送到远程
git push origin feature/add-league-column

# 4. 创建Pull Request
# 在GitHub上创建PR

# 5. 代码审查后合并到main
git checkout main
git pull origin main
git merge feature/add-league-column

# 6. 删除功能分支
git branch -d feature/add-league-column
git push origin --delete feature/add-league-column
```

---

## 📞 需要帮助？

- 问题反馈: [GitHub Issues](https://github.com/QooBeeLindor/jiumai-fantasy-sports/issues)
- Git文档: https://git-scm.com/doc
- 语义化版本: https://semver.org/

---

**记住**：好的提交信息是给未来的自己和团队成员最好的文档！📝

---

**最后更新**: 2026-01-24  
**版本**: v2.1.1
