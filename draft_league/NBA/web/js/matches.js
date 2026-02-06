const API_BASE = 'http://127.0.0.1:5001/api';

let allMatches = [];
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

// 加载周数选项
async function loadWeeks() {
    try {
        const response = await fetch(`${API_BASE}/stats`);
        const data = await response.json();
        
        const select = document.getElementById('week-filter');
        for (let i = data.current_week; i >= 1; i--) {
            const option = document.createElement('option');
            option.value = i;
            option.textContent = `第${i}周`;
            select.appendChild(option);
        }
        
        // 默认显示最新.current_week;
    } catch (error) {
        console.error('加载周数失败:', error);
    }
}

// 加载比赛记录
async function loadMatches() {
    try {
        const container = document.getElementById('matches-container');
        container.innerHTML = '<p style="text-align:center;">正在加载数据...</p>';
        
        const response = await fetch(`${API_BASE}/matches`);
        allMatches = await response.json();
        
        console.log('加载了', allMatches.length, '场比赛');
        renderMatches();
    } catch (error) {
        console.error('加载比赛记录失败:', error);
        document.getElementById('matches-container').innerHTML = 
            '<p style="text-align:center; color: red;">加载失败，请刷新页面</p>';
    }
}

// 渲染比赛记录
function renderMatches() {
    const weekFilter = document.getElementById('week-filter').value;
    const leagueFilter = document.getElementById('league-filter').value;
    
    let filtered = allMatches;
    
    if (weekFilter) {
        filtered = filtered.filter(m => m.week == weekFilter);
    }
    
    if (leagueFilter) {
        const selectedLeague = allLeagues.find(l => l.id == leagueFilter);
        if (selectedLeague) {
            filtered = filtered.filter(m => m.league_name === selectedLeague.name);
        }
    }
    
    const container = document.getElementById('matches-container');
    
    if (filtered.length === 0) {
        container.innerHTML = '<p style="text-align:center;">没有符合条件的比赛</p>';
        return;
    }
    
    // 按周和联赛分组
    const grouped = {};
    filtered.forEach(match => {
        const key = `Week ${match.week} - ${match.league_name}`;
        if (!grouped[key]) {
            grouped[key] = [];
        }
        grouped[key].push(match);
    });
    
    let html = '';
    Object.keys(grouped).sort().reverse().forEach(key => {
        html += `
            <div class="match-group">
                <h3>${key}</h3>
                <div class="matches-grid">
        `;
        
        grouped[key].forEach(match => {
            const winner1 = match.winner_id === match.player1_id ? 'winner' : '';
            const winner2 = match.winner_id === match.player2_id ? 'winner' : '';
            const isTie = match.score1 === match.score2;
            
            html += `
                <div class="match-card ${isTie ? 'tie' : ''}">
                    <div class="match-player ${winner1}">
                        <span class="player-name">${match.player1_name}</span>
                        <span class="score">${match.score1}</span>
                    </div>
                    <div class="match-vs">VS</div>
                    <div class="match-player ${winner2}">
                        <span class="player-name">${match.player2_name}</span>
                        <span class="score">${match.score2}</span>
                    </div>
                </div>
            `;
        });
        
        html += `
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

// 监听筛选器变化
document.addEventListener('DOMContentLoaded', () => {
    loadLeagues();
    loadWeeks();
    loadMatches();
    
    document.getElementById('week-filter').addEventListener('change', renderMatches);
    document.getElementById('league-filter').addEventListener('change', renderMatches);
});
