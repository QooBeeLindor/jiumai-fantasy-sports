import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Search, Filter, Trophy, TrendingUp, ExternalLink, Info, X } from 'lucide-react'
import { getOverallRotoRankings, getOverallRotoLeagues, getAllLeagueStandings } from '../services/api'

const OverallRotoPage = () => {
  const [rankings, setRankings] = useState([])
  const [leagues, setLeagues] = useState([])
  const [standingsMap, setStandingsMap] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  
  // Filters
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedLeague, setSelectedLeague] = useState('')
  const [limit, setLimit] = useState(200)
  const [sortField, setSortField] = useState('rank')
  const [sortDirection, setSortDirection] = useState('asc')
  
  // Modal
  const [selectedTeam, setSelectedTeam] = useState(null)
  const [showModal, setShowModal] = useState(false)
  
  useEffect(() => {
    fetchData()
  }, [selectedLeague, limit])
  
  const fetchData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const params = { limit }
      if (selectedLeague) {
        params.league = selectedLeague
      }
      
      const rankingsData = await getOverallRotoRankings(params)
      setRankings(rankingsData.data || [])
      
      const leaguesData = await getOverallRotoLeagues()
      setLeagues(leaguesData.data || [])
      
      const standingsData = await getAllLeagueStandings()
      setStandingsMap(standingsData.data || {})
      
    } catch (err) {
      console.error('Error fetching data:', err)
      setError('加载数据失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }
  
  const getMedal = (rank) => {
    if (rank === 1) return '🥇'
    if (rank === 2) return '🥈'
    if (rank === 3) return '🥉'
    return null
  }
  
  const getLeagueInfo = (teamKey) => {
    if (!teamKey || !standingsMap[teamKey]) {
      return { league_rank: '-', games_back: '-' }
    }
    return standingsMap[teamKey]
  }
  
  const filteredRankings = rankings
    .filter(team => {
      const matchesSearch = team.team_name.toLowerCase().includes(searchTerm.toLowerCase())
      return matchesSearch
    })
    .sort((a, b) => {
      let aValue, bValue
      
      switch (sortField) {
        case 'rank':
          aValue = a.rank
          bValue = b.rank
          break
        case 'team_name':
          aValue = a.team_name.toLowerCase()
          bValue = b.team_name.toLowerCase()
          break
        case 'league':
          aValue = a.league.toLowerCase()
          bValue = b.league.toLowerCase()
          break
        case 'total_roto_points':
          aValue = a.total_roto_points
          bValue = b.total_roto_points
          break
        case 'league_rank':
          const aInfo = getLeagueInfo(a.team_key)
          const bInfo = getLeagueInfo(b.team_key)
          aValue = aInfo.league_rank === '-' ? 999 : parseInt(aInfo.league_rank)
          bValue = bInfo.league_rank === '-' ? 999 : parseInt(bInfo.league_rank)
          break
        case 'games_back':
          const aInfoGB = getLeagueInfo(a.team_key)
          const bInfoGB = getLeagueInfo(b.team_key)
          aValue = aInfoGB.games_back === '-' ? 999 : parseFloat(aInfoGB.games_back)
          bValue = bInfoGB.games_back === '-' ? 999 : parseFloat(bInfoGB.games_back)
          break
        default:
          aValue = a.rank
          bValue = b.rank
      }
      
      if (sortDirection === 'asc') {
        return aValue > bValue ? 1 : -1
      } else {
        return aValue < bValue ? 1 : -1
      }
    })
  
  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('asc')
    }
  }
  
  const openModal = (team) => {
    setSelectedTeam(team)
    setShowModal(true)
  }
  
  const closeModal = () => {
    setShowModal(false)
    setSelectedTeam(null)
  }
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center space-y-4">
          <div className="w-16 h-16 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="text-gray-600 font-medium">加载中...</p>
        </div>
      </div>
    )
  }
  
  if (error) {
    return (
      <div className="card p-8 text-center">
        <div className="text-red-500 text-5xl mb-4">⚠️</div>
        <h3 className="text-xl font-bold text-gray-800 mb-2">加载失败</h3>
        <p className="text-gray-600 mb-4">{error}</p>
        <button onClick={fetchData} className="btn btn-primary">
          重试
        </button>
      </div>
    )
  }
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="card p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-gradient-to-br from-primary-500 to-secondary-500 rounded-xl shadow-md">
              <Trophy className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-800">Overall Roto Rankings</h1>
              <p className="text-gray-600 mt-1">跨12个联赛的综合Roto积分排名</p>
            </div>
          </div>
          
          <div className="text-right">
            <div className="text-3xl font-bold text-gradient">{rankings.length}</div>
            <div className="text-sm text-gray-500">支球队</div>
          </div>
        </div>
      </div>
      
      {/* Filters */}
      <div className="card p-6 space-y-4">
        <div className="flex items-center space-x-2 text-gray-700 mb-2">
          <Filter className="w-5 h-5" />
          <span className="font-semibold">筛选和搜索</span>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="搜索球队名称..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
          
          <select
            value={selectedLeague}
            onChange={(e) => setSelectedLeague(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          >
            <option value="">所有联赛</option>
            {leagues.map(league => (
              <option key={league.id} value={league.name}>
                {league.name}
              </option>
            ))}
          </select>
          
          <select
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          >
            <option value={50}>前50名</option>
            <option value={100}>前100名</option>
            <option value={200}>全部显示</option>
          </select>
        </div>
        
        <div className="text-sm text-gray-500">
          显示 <span className="font-semibold text-primary-600">{filteredRankings.length}</span> 支球队
        </div>
      </div>
      
      {/* Rankings Table */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gradient-to-r from-gray-50 to-gray-100 border-b-2 border-gray-200">
              <tr>
                <th className="px-6 py-4 text-left">
                  <button
                    onClick={() => handleSort('rank')}
                    className="flex items-center space-x-1 font-semibold text-gray-700 hover:text-primary-600"
                  >
                    <span>Overall排名</span>
                    {sortField === 'rank' && (
                      <span className="text-primary-600">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                    )}
                  </button>
                </th>
                <th className="px-6 py-4 text-left">
                  <button
                    onClick={() => handleSort('league_rank')}
                    className="flex items-center space-x-1 font-semibold text-gray-700 hover:text-primary-600"
                  >
                    <span>联赛排名</span>
                    {sortField === 'league_rank' && (
                      <span className="text-primary-600">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                    )}
                  </button>
                </th>
                <th className="px-6 py-4 text-left">
                  <button
                    onClick={() => handleSort('team_name')}
                    className="flex items-center space-x-1 font-semibold text-gray-700 hover:text-primary-600"
                  >
                    <span>球队名称</span>
                    {sortField === 'team_name' && (
                      <span className="text-primary-600">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                    )}
                  </button>
                </th>
                <th className="px-6 py-4 text-left">
                  <button
                    onClick={() => handleSort('league')}
                    className="flex items-center space-x-1 font-semibold text-gray-700 hover:text-primary-600"
                  >
                    <span>联赛</span>
                    {sortField === 'league' && (
                      <span className="text-primary-600">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                    )}
                  </button>
                </th>
                <th className="px-6 py-4 text-right">
                  <button
                    onClick={() => handleSort('total_roto_points')}
                    className="flex items-center justify-end space-x-1 font-semibold text-gray-700 hover:text-primary-600 w-full"
                  >
                    <span>Roto积分</span>
                    {sortField === 'total_roto_points' && (
                      <span className="text-primary-600">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                    )}
                  </button>
                </th>
                <th className="px-6 py-4 text-center">
                  <button
                    onClick={() => handleSort('games_back')}
                    className="flex items-center justify-center space-x-1 font-semibold text-gray-700 hover:text-primary-600 w-full"
                  >
                    <span>GB</span>
                    {sortField === 'games_back' && (
                      <span className="text-primary-600">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                    )}
                  </button>
                </th>
                <th className="px-6 py-4 text-center font-semibold text-gray-700">详情</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {filteredRankings.map((team) => {
                const medal = getMedal(team.rank)
                const leagueInfo = getLeagueInfo(team.team_key)
                
                return (
                  <tr key={team.rank} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center space-x-2">
                        {medal && <span className="text-2xl">{medal}</span>}
                        <span className={`text-lg font-bold ${medal ? 'text-gradient' : 'text-gray-700'}`}>
                          #{team.rank}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <span className="inline-flex items-center justify-center min-w-[2rem] h-8 px-3 rounded-full bg-blue-100 text-blue-800 font-semibold">
                        {leagueInfo.league_rank}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="font-semibold text-gray-800">{team.team_name}</div>
                    </td>
                    <td className="px-6 py-4">
                      <Link
                        to={`/league/${team.league_id}`}
                        className="inline-flex items-center space-x-1 text-primary-600 hover:text-primary-700 font-medium"
                      >
                        <span>{team.league}</span>
                        <ExternalLink className="w-3 h-3" />
                      </Link>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <span className="font-bold text-lg text-primary-600">
                        {team.total_roto_points.toFixed(2)}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <span className={`font-semibold ${
                        leagueInfo.games_back === '0.0' || leagueInfo.games_back === '-'
                          ? 'text-green-600'
                          : 'text-red-600'
                      }`}>
                        {leagueInfo.games_back}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <button
                        onClick={() => openModal(team)}
                        className="text-primary-600 hover:text-primary-700 font-medium"
                      >
                        查看详情
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
      
      {/* Roto积分计算说明 */}
      <div className="card p-6 bg-blue-50 border border-blue-200">
        <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center space-x-2">
          <TrendingUp className="w-5 h-5 text-primary-600" />
          <span>Roto积分计算方法</span>
        </h3>
        
        <div className="space-y-3 text-gray-700">
          <div>
            <span className="font-semibold text-gray-800">基本规则：</span>
            <span className="ml-2">192个team在11个统计项目中分别排名，第1名得192分，第2名得191分...第192名得1分。</span>
          </div>
          
          <div>
            <span className="font-semibold text-gray-800">11个比项：</span>
            <span className="ml-2">FG%、FT%、3PTM、PTS、OREB、REB、AST、ST、BLK、TO（越低越好）、A/T</span>
          </div>
          
          <div>
            <span className="font-semibold text-gray-800">总Roto积分 = </span>
            <span className="ml-2">FG%积分 + FT%积分 + 3PTM积分 + ... + A/T积分（11项之和）</span>
          </div>
          
          <div>
            <span className="font-semibold text-gray-800">数据相同处理：</span>
            <span className="ml-2">多人并列时平分积分。例如4人并列第1，则积分为(192+191+190+189)/4=190.5分</span>
          </div>
          
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mt-4">
            <span className="font-semibold text-yellow-800">⚠️ 说明：</span>
            <span className="ml-2 text-gray-700">
              本Roto积分本质图一乐，不能反应真实状况。NBA H2H范特西联赛有清洁流、暴力流、控分流等众多流派，追求优势的比项和程度都不一样。
            </span>
          </div>
        </div>
      </div>
      
      {/* Team Detail Modal */}
      {showModal && selectedTeam && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-gradient-to-r from-primary-500 to-secondary-500 text-white p-6 rounded-t-2xl">
              <div className="flex justify-between items-start">
                <div>
                  <h2 className="text-2xl font-bold mb-1">{selectedTeam.team_name}</h2>
                  <p className="text-white/90">联赛: {selectedTeam.league}</p>
                </div>
                <button
                  onClick={closeModal}
                  className="p-2 hover:bg-white/20 rounded-lg transition-colors"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>
            </div>
            
            <div className="p-6 space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-gradient-to-br from-yellow-50 to-orange-50 p-4 rounded-xl border border-yellow-200">
                  <div className="text-sm text-gray-600 mb-1">Overall排名</div>
                  <div className="text-3xl font-bold text-gradient">#{selectedTeam.rank}</div>
                </div>
                <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-4 rounded-xl border border-blue-200">
                  <div className="text-sm text-gray-600 mb-1">Roto总分</div>
                  <div className="text-3xl font-bold text-primary-600">
                    {selectedTeam.total_roto_points.toFixed(2)}
                  </div>
                </div>
              </div>
              
              <div>
                <h3 className="text-lg font-bold text-gray-800 mb-3 flex items-center space-x-2">
                  <TrendingUp className="w-5 h-5 text-primary-600" />
                  <span>各项数据排名</span>
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {Object.entries(selectedTeam.stats).map(([stat, data]) => (
                    <div key={stat} className="bg-gray-50 p-3 rounded-lg border border-gray-200">
                      <div className="text-xs text-gray-500 mb-1">{stat}</div>
                      <div className="flex items-baseline space-x-2">
                        <span className="text-lg font-bold text-gray-800">#{data.rank}</span>
                        <span className="text-sm text-gray-600">({data.points}分)</span>
                      </div>
                      <div className="text-xs text-gray-500 mt-1">值: {data.value}</div>
                    </div>
                  ))}
                </div>
              </div>
              
              <div className="bg-blue-50 p-4 rounded-xl border border-blue-200">
                <h3 className="text-lg font-bold text-gray-800 mb-3">联赛信息</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-gray-600">联赛名称</div>
                    <Link
                      to={`/league/${selectedTeam.league_id}`}
                      className="font-semibold text-primary-600 hover:text-primary-700 flex items-center space-x-1"
                    >
                      <span>{selectedTeam.league}</span>
                      <ExternalLink className="w-3 h-3" />
                    </Link>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600">联赛ID</div>
                    <div className="font-semibold text-gray-800">{selectedTeam.league_id}</div>
                  </div>
                  {selectedTeam.team_key && (
                    <>
                      <div>
                        <div className="text-sm text-gray-600">联赛排名</div>
                        <div className="font-semibold text-gray-800">
                          {getLeagueInfo(selectedTeam.team_key).league_rank}
                        </div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-600">GB</div>
                        <div className={`font-semibold ${
                          getLeagueInfo(selectedTeam.team_key).games_back === '0.0'
                            ? 'text-green-600'
                            : 'text-red-600'
                        }`}>
                          {getLeagueInfo(selectedTeam.team_key).games_back}
                        </div>
                      </div>
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default OverallRotoPage
