// web/js/player.js
const API_BASE = 'http://127.0.0.1:5001/api';

// 从URL获取玩家ID
function getPlayerIdFromURL() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('id');
}

// 加载玩家数据
async function loadPlayerData() {
    const playerId = getPlayerIdFromURL();
    
    if (!playerId) {
        document.body.innerHTML = '<div style="text-align:center;padding:50px;"><h1>错误：缺少玩家ID</h1></div>';
        return;
    }
    
    try {
        console.log(`加载玩家 ID: ${playerId}`);
        const response = await fetch(`${API_BASE}/player/${playerId}`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        console.log('玩家数据:', data);
        
        renderPlayerData(data);
    } catch (error) {
        console.error('加载玩家数据失败:', error);
        document.body.innerHTML = `
            <div style="text-align:center;padding:50px;">
                <h1>加载失败</h1>
                <p>${error.message}</p>
                <p>请确保API服务正在运行 (python api.py)</p>
                <a href="index.html">返回首页</a>
            </div>
        `;
    }
}

// 渲染玩家数据
function renderPlayerData(data) {
    const player = data.player;
    const leagues = data.leagues || [];
    const eloHistory = data.elo_history || [];
    
    // 更新玩家名称
    const nameElement = document.querySelector('.player-name');
    if (nameElement) {
        nameElement.textContent = player.unified_name || '未知玩家';
    }
    
    // 更新ELO
    const eloElement = document.querySelector('.elo-value');
    if (eloElement) {
        eloElement.textContent = Math.round(player.elo_rating || 0);
    }
    
    // 计算总战绩
    let totalWins = 0;
    let totalLosses = 0;
    let totalTies = 0;
    let totalMatches = 0;
    
    leagues.forEach(league => {
        totalWins += league.wins || 0;
        totalLosses += league.losses || 0;
        totalTies += league.ties || 0;
        totalMatches += league.matches_played || 0;
    });
    
    const winRate = totalMatches > 0 ? (totalWins / totalMatches * 100).toFixed(1) : 0;
    
    // 更新统计卡片
    updateStatCard('wins', totalWins);
    updateStatCard('losses', totalLosses);
    updateStatCard('ties', totalTies);
    updateStatCard('win-rate', `${winRate}%`);
    
    // 更新联盟信息
    if (leagues.length > 0) {
        const mainLeague = leagues[0];
        updateStatCard('tier', `Tier ${mainLeague.tier}`);
        updateStatCard('draft-position', `#${mainLeague.draft_position || '-'}`);
    }
    
    // 渲染联盟列表
    renderLeagues(leagues);
    
    // 渲染ELO历史
    renderEloHistory(eloHistory);
}

// 更新统计卡片
function updateStatCard(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value;
    }
}

// 渲染联盟列表
function renderLeagues(leagues) {
    const container = document.getElementById('leagues-container');
    if (!container) return;
    
    if (leagues.length === 0) {
        container.innerHTML = '<p>暂无联盟数据</p>';
        return;
    }
    
    container.innerHTML = leagues.map(league => `
        <div class="league-item">
            <h3>${league.league_name}</h3>
            <p>Tier ${league.tier} | 顺位 #${league.draft_position || '-'}</p>
            <p>战绩: ${league.wins}-${league.losses}-${league.ties} (${league.matches_played}场)</p>
        </div>
    `).join('');
}

// 渲染ELO历史
function renderEloHistory(history) {
    const container = document.getElementById('elo-history-container');
    if (!container) return;
    
    if (history.length === 0) {
        container.innerHTML = '<p>暂无对战记录</p>';
        return;
    }
    
    container.innerHTML = history.map(item => {
        const resultClass = item.result === 'WIN' ? 'win' : (item.result === 'LOSS' ? 'loss' : 'tie');
        const resultText = item.result === 'WIN' ? '胜' : (item.result === 'LOSS' ? '负' : '平');
        const eloChange = item.elo_change >= 0 ? `+${item.elo_change.toFixed(1)}` : item.elo_change.toFixed(1);
        
        return `
            <div class="history-item ${resultClass}">
                <div class="history-week">Week ${item.week}</div>
                <div class="history-league">${item.league_name}</div>
                <div class="history-opponent">vs ${item.opponent_name}</div>
                <div class="history-result">${resultText}</div>
                <div class="history-elo">
                    ${Math.round(item.elo_before)} → ${Math.round(item.elo_after)} 
                    <span class="elo-change">(${eloChange})</span>
                </div>
            </div>
        `;
    }).join('');
}

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', loadPlayerData);
