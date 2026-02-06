const API_BASE = 'http://127.0.0.1:5001/api';

let allLeagues = [];
let allRankings = [];

// 加载数据
async function loadData() {
    try {
        const [leaguesRes, rankingsRes] = await Promise.all([
            fetch(`${API_BASE}/leagues`),
            fetch(`${API_BASE}/rankings`)
        ]);
        
        allLeagues = await leaguesRes.json();
        allRankings = await rankingsRes.json();
        
        renderLeagues();
        renderChart();
    } catch (error) {
        console.error('加载数据失败:', error);
        document.getElementById('leagues-container').innerHTML = 
            '<p style="text-align:center; color: red;">加载失败，请刷新页面</p>';
    }
}

// 计算联赛统计数据
function getLeagueStats(leagueName) {
    const players = allRankings.filter(p => p.league_name === leagueName);
    
    if (players.length === 0) {
        return {
            avgElo: 0,
            maxElo: 0,
            minElo: 0,
            playerCount: 0
        };
    }
    
    const elos = players.map(p => p.elo_rating);
    return {
        avgElo: Math.round(elos.reduce((a, b) => a + b, 0) / elos.length),
        maxElo: Math.round(Math.max(...elos)),
        minElo: Math.round(Math.min(...elos)),
        playerCount: players.length
    };
}

// 渲染联赛卡片
function renderLeagues() {
    const container = document.getElementById('leagues-container');
    
    const html = allLeagues.map(league => {
        const stats = getLeagueStats(league.name);
        
        return `
            <div class="league-card tier-${league.tier}">
                <h3>${league.name}</h3>
                <div class="league-tier">级别：Tier ${league.tier}</div>
                <div class="league-stats">
                    <div class="stat-item">
                        <span class="stat-label">平均ELO</span>
                        <span class="stat-value">${stats.avgElo}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">最高ELO</span>
                        <span class="stat-value">${stats.maxElo}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">最低ELO</span>
                        <span class="stat-value">${stats.minElo}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">玩家数</span>
                        <span class="stat-value">${stats.playerCount}</span>
                    </div>
                </div>
            </div>
        `;
    }).join('');
    
    container.innerHTML = html;
}

// 渲染图表
function renderChart() {
    const tierStats = {};
    
    // 按级别统计
    for (let tier = 1; tier <= 4; tier++) {
        const tierPlayers = allRankings.filter(p => p.tier === tier);
        if (tierPlayers.length > 0) {
            const avgElo = tierPlayers.reduce((sum, p) => sum + p.elo_rating, 0) / tierPlayers.length;
            tierStats[tier] = Math.round(avgElo);
        } else {
            tierStats[tier] = 0;
        }
    }
    
    const ctx = document.getElementById('tierChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['一级盟', '二级盟', '三级盟', '四级盟'],
            datasets: [{
                label: '平均ELO',
                data: [tierStats[1], tierStats[2], tierStats[3], tierStats[4]],
                backgroundColor: [
                    'rgba(240, 147, 251, 0.7)',
                    'rgba(79, 172, 254, 0.7)',
                    'rgba(67, 233, 123, 0.7)',
                    'rgba(250, 112, 154, 0.7)'
                ],
                borderColor: [
                    'rgb(240, 147, 251)',
                    'rgb(79, 172, 254)',
                    'rgb(67, 233, 123)',
                    'rgb(250, 112, 154)'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                y: {
                    beginAtZero: false,
                    min: 1300,
                    max: 1700,
                    title: {
                        display: true,
                        text: 'ELO积分'
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                title: {
                    display: true,
                    text: '各级别平均实力对比',
                    font: {
                        size: 18
                    }
                }
            }
        }
    });
}

// 页面加载
document.addEventListener('DOMContentLoaded', loadData);
