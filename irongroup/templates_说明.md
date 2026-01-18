# 📁 templates_irongroup 文件夹

## 包含的文件

这个文件夹包含3个HTML模板文件，需要放在 `G:\irongroup\templates\` 目录下：

1. **landing.html** (3.2KB)
   - 团队赛落地页
   - 显示🏆图标和"查看排行榜"按钮

2. **leaderboard.html** (9.5KB)
   - 团队排行榜页面
   - 显示12个团队的排名和各项目得分
   - 包含搜索功能

3. **team_detail.html** (9.0KB)
   - 团队详情页
   - 显示团队成员和各项目得分详情

## 使用方法

### 方法1：手动创建

1. 在 `G:\irongroup\` 下创建 `templates` 文件夹
2. 将下载的 `templates_irongroup` 文件夹中的3个HTML文件复制到 `templates` 文件夹

```
G:\irongroup\
└── templates\
    ├── landing.html
    ├── leaderboard.html
    └── team_detail.html
```

### 方法2：重命名

1. 将下载的 `templates_irongroup` 文件夹重命名为 `templates`
2. 移动到 `G:\irongroup\` 下

```
下载的 templates_irongroup → 重命名为 templates → 移动到 G:\irongroup\
```

## 验证

文件夹结构应该是：

```
G:\irongroup\
├── irongroup_app.py
├── irongroup.db
├── irongroup_database.sql
├── import_irongroup_data.py
├── 2526铁人团队赛.xlsx
└── templates\              ← 必须是这个名字
    ├── landing.html        ← 3个HTML文件
    ├── leaderboard.html
    └── team_detail.html
```

如果 `templates` 文件夹或HTML文件不在正确位置，Flask会报错：`TemplateNotFound`

## 注意

- 文件夹名必须是 `templates`（不是 templates_irongroup）
- 必须放在 `irongroup_app.py` 同级目录下
- HTML文件名不能改
