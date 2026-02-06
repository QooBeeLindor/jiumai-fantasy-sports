const API_BASE = 'http://127.0.0.1:5001/api';

// 加载统计数据
async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/stats`);
        const data = await response.json();
        
        const statsHtml = `
            <div class="stat-card">
                <h3>${data.current_week}</h3>
                <p>当前周数</p>
            </div>
            <div class="stat-card">
                <h3>${data.total_matches}</h3>
                <p>总比赛数</p>
            </div>
            <div class="stat-card">
                <h3>${data.total_players}</h3>
                <p>参赛玩家</p>
            </div>
            <div class="stat-card">
                <h3>${data.total_leagues}</h3>
                <p>联赛数量</p>
            </div>
        `;
        
        document.getElementById('stats').innerHTML = statsHtml;
    } catch (error) {
        console.error('加载统计数据失败:', error);
    }
}

// 加载排行榜
async function loadRankings(limit = 10) {
    try {
        const response = await fetch(`${API_BASE}/rankings`);
        const data = await response.json();
        
        const tbody = document.querySelector('#rankings-table tbody');
        tbody.innerHTML = data.slice(0, limit).map((player, index) => `
            <tr>
                <td><strong>${index + 1}</strong></td>
                <td>${player.display_name}</td>
                <td>${player.league_name}</td>
                <td><strong>${Math.round(player.elo_rating)}</strong></td>
                <td>Tier ${player.tier}</td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('加载排行榜失败:', error);
        document.querySelector('#rankings-table tbody').innerHTML = 
            '<tr><td colspan="5">加载失败，请刷新页面</td></tr>';
    }
}

// 页面加载时执行
document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    loadRankings();
});
