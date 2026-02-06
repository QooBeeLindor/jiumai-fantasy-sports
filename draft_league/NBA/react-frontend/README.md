# NBA Draft League - React Frontend

## 🚀 快速开始

### 安装依赖
```bash
npm install
```

### 启动开发服务器
```bash
npm run dev
```

访问：http://localhost:3000

### 构建生产版本
```bash
npm run build
```

---

## 📋 前提条件

1. **Node.js** - 版本 16+ 
2. **后端API运行中** - http://localhost:5003

---

## 🔧 配置

### API地址配置

编辑 `.env` 文件：
```env
VITE_API_URL=http://localhost:5003
```

生产环境修改为实际的API地址。

---

## 📁 项目结构

```
react-frontend/
├── src/
│   ├── components/         # 组件
│   │   └── Layout.jsx      # 页面布局
│   ├── pages/              # 页面
│   │   ├── HomePage.jsx    # 首页
│   │   ├── OverallRotoPage.jsx    # 总排名
│   │   └── LeagueDetailPage.jsx   # 分盟详细
│   ├── services/           # 服务
│   │   └── api.js          # API客户端
│   ├── App.jsx             # 应用入口
│   ├── main.jsx            # 主文件
│   └── index.css           # 全局样式
├── package.json            # 依赖配置
├── vite.config.js          # Vite配置
├── tailwind.config.js      # Tailwind配置
└── index.html              # HTML模板
```

---

## 🎨 技术栈

- **React 18** - UI框架
- **Vite** - 构建工具
- **Tailwind CSS** - 样式框架
- **React Router** - 路由
- **Axios** - HTTP客户端
- **Lucide React** - 图标库

---

## 🌐 路由

- `/` - 首页
- `/overall-roto` - Overall Roto总排名
- `/league/:leagueId` - 分盟详细页面

---

## 📡 API集成

所有API调用在 `src/services/api.js` 中：

```javascript
import { getOverallRotoRankings } from './services/api'

// 获取排名
const data = await getOverallRotoRankings({ limit: 200 })
```

---

## 🎯 功能特性

### Overall Roto Rankings 页面
- ✅ 192支球队排名
- ✅ 搜索和筛选
- ✅ 可排序表格
- ✅ Team详情模态框
- ✅ 联赛链接

### League Detail 页面
- ✅ 联赛内排名
- ✅ Overall排名对比
- ✅ Games Back数据
- ✅ 统计信息卡片

### 响应式设计
- ✅ 移动端适配
- ✅ 平板端适配
- ✅ 桌面端优化

---

## 🐛 故障排除

### 问题1：npm install 失败
```bash
npm cache clean --force
npm install
```

### 问题2：API连接失败
- 确认后端API在运行
- 检查 `.env` 中的API地址
- 检查防火墙设置

### 问题3：端口3000被占用
修改 `vite.config.js`：
```javascript
server: {
  port: 3001  // 改为其他端口
}
```

### 问题4：样式不显示
```bash
# 重新安装Tailwind
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

---

## 📦 部署

### 构建
```bash
npm run build
```

输出目录：`dist/`

### 部署到Nginx
```bash
# 复制构建文件
cp -r dist/* /var/www/html/

# Nginx配置
location / {
  try_files $uri $uri/ /index.html;
}

location /api {
  proxy_pass http://localhost:5003;
}
```

### 部署到Vercel
```bash
npm install -g vercel
vercel --prod
```

---

## 📞 帮助

如有问题，请查看：
- `REACT_FRONTEND_INSTALL_GUIDE.md` - 详细安装指南
- `PROJECT_FINAL_SUMMARY.md` - 项目总结
- `QUICK_START_GUIDE.md` - 快速开始

---

## ✅ 验证清单

- [ ] Node.js 已安装（16+）
- [ ] 后端API正在运行（5003端口）
- [ ] `npm install` 成功
- [ ] `npm run dev` 启动成功
- [ ] 浏览器访问 http://localhost:3000
- [ ] 能看到首页
- [ ] 能访问总排名页面
- [ ] 能访问分盟详细页面

---

**Made with ❤️ for NBA Draft League**

Version: 1.0.0
Date: 2026-02-05
