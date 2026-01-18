# 九麦NBA竞价选秀范特西联赛 - ELO排名系统 V2.0

## 功能特性

### Phase 1 (当前版本)
- ✅ 北斗五星联赛命名 (天枢、天璇、天玑、天权、玉衡)
- ✅ ELO总排行榜
- ✅ 五盟详细对比
- ✅ 每周ELO变化表格
- ✅ 玩家详情和历史
- ✅ 比赛记录查询
- ✅ Windows兼容性优化

## 快速启动

1. 确保数据库文件存在:
   ```bash
   copy G:\nba_elo_system\nba_elo.db web_app_v2\
   ```

2. 安装依赖:
   ```bash
   pip install Flask
   ```

3. 运行应用:
   ```bash
   python app.py
   ```

4. 访问:
   ```
   http://127.0.0.1:5000
   ```

## 页面导航

- `/` - ELO总排行榜
- `/leagues` - 五盟对比
- `/matches` - 比赛记录
- `/weekly_elo` - 每周变化
- `/player/<id>` - 玩家详情
- `/api/rankings` - API接口

## 联赛配置

```python
LEAGUE_NAMES = {
    162274: '天枢盟',
    162271: '天璇盟',  
    161296: '天玑盟',
    161323: '天权盟',
    161314: '玉衡盟',
}
```

## 未来功能 (Phase 2+)

- [ ] 玩家阵容展示 (Yahoo API)
- [ ] 球员持有率统计
- [ ] 跨联赛玩家识别
- [ ] NHL/MLB/NFL数据导入
- [ ] 铁人联赛积分系统

---

*九麦范特西联赛 - 2026*
