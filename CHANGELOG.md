# Changelog

All notable changes to NBA ELO System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2026-01-21

### Added
- **PrefixMiddleware**: 新增中间件支持Flask应用部署在子路径下（如 `/NBA/waiverleague/`）
  - 自动读取Nginx传递的 `X-Script-Name` header
  - 动态设置Flask的 `SCRIPT_NAME` 环境变量
  - 自动调整 `PATH_INFO` 以适配子路径部署

### Changed
- **URL生成方式标准化**：所有模板统一使用 `url_for()` 生成URL，替代硬编码路径
- **templates/index.html**:
  - 玩家详情链接从 `/player/...` 改为 `url_for('player_detail', ...)`
  - 阵容链接从 `/roster/...` 改为 `url_for('roster', ...)`
- **templates/player.html**:
  - 阵容链接从 `/roster/...` 改为 `url_for('roster', ...)`

### Fixed
- 修复应用部署在子路径时，导航栏链接指向错误路径的问题
- 修复玩家详情页（/player/...）无法访问的问题
- 修复球队阵容页（/roster/...）无法访问的问题
- 修复首页玩家列表点击跳转到错误路径的问题

### Technical Details
- **部署路径**：应用现在正确支持部署在 `/NBA/waiverleague/` 子路径
- **兼容性**：向后兼容，在根路径部署时仍能正常工作
- **架构**：Nginx → Gunicorn → Flask + PrefixMiddleware

### Deployment
- 使用Supervisor管理应用进程
- Gunicorn作为WSGI服务器（2 workers）
- Nginx作为反向代理，设置 `X-Script-Name` header

### Breaking Changes
无破坏性变更。所有修改向后兼容。

---

## [2.0.0] - 2026-01-XX (Previous Version)

### Features
- ELO排名系统
- 联赛对比功能
- 比赛记录查询
- 每周ELO变化追踪
- 玩家详情页面
- 球队阵容查看
- 算法详解页面

### Technical Stack
- Backend: Flask (Python)
- Database: SQLite
- Frontend: Bootstrap 5, Chart.js
- Deployment: Nginx + Gunicorn + Supervisor

---

## Migration Guide

### From 2.0.x to 2.1.0

如果你从旧版本升级，需要：

1. **更新 app.py**
   ```bash
   # 在应用初始化部分添加中间件
   app.wsgi_app = PrefixMiddleware(app.wsgi_app)
   ```

2. **更新模板文件**
   - 检查所有模板中的硬编码路径
   - 将 `href="/path/..."` 改为 `href="{{ url_for('route_name', ...) }}"`
   - 将 `onclick="window.location='/path/...'"` 改为 `onclick="window.location='{{ url_for(...) }}'"`

3. **更新Nginx配置**（如果使用子路径部署）
   ```nginx
   location /NBA/waiverleague/ {
       proxy_pass http://127.0.0.1:5000/;
       proxy_set_header X-Script-Name /NBA/waiverleague;
       # ... 其他配置
   }
   ```

4. **重启应用**
   ```bash
   sudo supervisorctl restart nba_elo
   ```

### Verification
部署后验证以下URL：
- ✅ `/NBA/waiverleague/`
- ✅ `/NBA/waiverleague/leagues`
- ✅ `/NBA/waiverleague/matches`
- ✅ `/NBA/waiverleague/weekly_elo`
- ✅ `/NBA/waiverleague/algorithm`
- ✅ `/NBA/waiverleague/player/<player_id>`
- ✅ `/NBA/waiverleague/roster/<league_id>/<team_key>`
