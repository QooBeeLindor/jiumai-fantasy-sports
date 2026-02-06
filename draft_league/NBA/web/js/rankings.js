const API_BASE = 'http://127.0.0.1:5001/api';

let allRankings = [];
let allLeagues = [];

// 加载联赛列表
async function loadLeagues() {
    try {
        const response = await fetch(`${API_BASE}/leagues`);
        allLeagues = await response.json();
        
        const select = document.getElementById('league-filter');
        allLeagues.forEach(league => {
            const option = document.createElement('option');
            option.value = league.id;
            option.textContent = league.name;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('加载联赛列表失败:', error);
    }
}

// 加载排行榜
async function loadRankings() {
    try {
        const tbody = document.querySelector('#rankings-table tbody');
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;">正在加载数据...</td></tr>';
        
        const response = await fetch(`${API_BASE}/rankings`);
        allRankings = await response.json();
        
        console.log('加载了', allRankings.length, '名玩家');
        renderRankings();
    } catch (error) {
        console.error('加载排行榜失败:', error);
        document.querySelector('#rankings-table tbody').innerHTML = 
            '<tr><td colspan="6" style="text-align:center; color: red;">加载失败，请刷新页面</td></tr>';
    }
}

// 渲染排行榜
function renderRankings() {
    const leagueFilter = document.getElementById('league-filter').value;
    const tierFilter = document.getElementById('tier-filter').value;
    
    let filtered = allRankings;
    
    if (leagueFilter) {
        const selectedLeague = allLeagues.find(l => l.id == leagueFilter);
        if (selectedLeague) {
            filtered = filtered.filter(p => p.league_name === selectedLeague.name);
        }
    }
    
    if (tierFilter) {
        filtered = filtered.filter(p => p.tier == tierFilter);
    }
    
    const tbody = document.querySelector('#rankings-table tbody');
    
    if (filtered.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;">没有符合条件的数据</td></tr>';
        return;
    }
    
    tbody.innerHTML = filtered.map((player, index) => `
        <tr>
            <td><strong>${index + 1}</strong></td>
            <td><a href="player.html?id=${player.id}" class="player-link">${player.display_name || '未知'}</a></td>
            <td>${player.league_name || '未知'}</td>
            <td>Tier ${player.tier}</td>
            <td>#${player.draft_position}</td>
            <td><strong>${Math.round(player.elo_rating)}</strong></td>
        </tr>
    `).join('');
}

// 监听筛选器变化
document.addEventListener('DOMContentLoaded', () => {
    loadLeagues();
    loadRankings();
    
    document.getElementById('league-filter').addEventListener('change', renderRankings);
    document.getElementById('tier-filter').addEventListener('change', renderRankings);
});
