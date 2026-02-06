import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Trophy, TrendingUp, Users, Info, X } from 'lucide-react'
import { getLeagueDetail } from '../services/api'

const LeagueDetailPage = () => {
  const { leagueId } = useParams()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [sortField, setSortField] = useState('overall_rank')
  const [sortDirection, setSortDirection] = useState('asc')
  const [selectedTeam, setSelectedTeam] = useState(null)
  const [showModal, setShowModal] = useState(false)
  
  useEffect(() => {
    fetchData()
  }, [leagueId])
  
  const fetchData = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await getLeagueDetail(leagueId)
      setData(response.data)
    } catch (err) {
      console.error('Error fetching league detail:', err)
      setError('加载数据失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }
  
  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('asc')
    }
  }
  
  const sortedTeams = data?.teams ? [...data.teams].sort((a, b) => {
    let aValue, bValue
    
    switch (sortField) {
      case 'overall_rank':
        aValue = a.overall_rank
        bValue = b.overall_rank
        break
      case 'team_name':
        aValue = a.team_name.toLowerCase()
        bValue = b.team_name.toLowerCase()
        break
      case 'manager':
        aValue = a.manager.toLowerCase()
        bValue = b.manager.toLowerCase()
        break
      case 'total_roto_points':
        aValue = a.total_roto_points
        bValue = b.total_roto_points
        break
      case 'league_rank':
        aValue = a.league_rank
        bValue = b.league_rank
        break
      case 'games_back':
        aValue = parseFloat(a.games_back)
        bValue = parseFloat(b.games_back)
        break
      default:
        aValue = a.overall_rank
        bValue = b.overall_rank
    }
    
    if (sortDirection === 'asc') {
      return aValue > bValue ? 1 : -1
    } else {
      return aValue < bValue ? 1 : -1
    }
  }) : []
  
  const getMedal = (rank) => {
    if (rank === 1) return '🥇'
    if (rank === 2) return '🥈'
    if (rank === 3) return '🥉'
    return null
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
  
  if (error || !data) {
    return (
      <div className="card p-8 text-center">
        <div className="text-red-500 text-5xl mb-4">⚠️</div>
        <h3 className="text-xl font-bold text-gray-800 mb-2">加载失败</h3>
        <p className="text-gray-600 mb-4">{error || '未找到联赛数据'}</p>
        <div className="flex justify-center space-x-4">
          <Link to="/overall-roto" className="btn btn-primary">
            返回总排名
          </Link>
          <button onClick={fetchData} className="btn btn-secondary">
            重试
          </button>
        </div>
      </div>
    )
  }
  
  return (
    <div className="space-y-6">
      {/* Back Button */}
      <Link
        to="/overall-roto"
        className="inline-flex items-center space-x-2 text-primary-600 hover:text-primary-700 font-medium"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>返回总排名</span>
      </Link>
      
      {/* Header */}
      <div className="card p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-gradient-to-br from-primary-500 to-secondary-500 rounded-xl shadow-md">
              <Trophy className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-800">{data.league_name}</h1>
              <p className="text-gray-600 mt-1">联赛ID: {data.league_id}</p>
            </div>
          </div>
        </div>
      </div>
      
      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="card p-4">
          <div className="flex items-center space-x-3">
            <Users className="w-8 h-8 text-primary-500" />
            <div>
              <div className="text-2xl font-bold text-gray-800">{data.stats.total_teams}</div>
              <div className="text-sm text-gray-500">球队数量</div>
            </div>
          </div>
        </div>
        
        <div className="card p-4">
          <div>
            <div className="text-sm text-gray-500 mb-1">平均Roto积分</div>
            <div className="text-2xl font-bold text-primary-600">
              {data.stats.avg_roto_points.toFixed(2)}
            </div>
          </div>
        </div>
        
        <div className="card p-4">
          <div>
            <div className="text-sm text-gray-500 mb-1">最高Roto积分</div>
            <div className="text-2xl font-bold text-green-600">
              {data.stats.max_roto_points.toFixed(2)}
            </div>
          </div>
        </div>
        
        <div className="card p-4">
          <div>
            <div className="text-sm text-gray-500 mb-1">最低Roto积分</div>
            <div className="text-2xl font-bold text-red-600">
              {data.stats.min_roto_points.toFixed(2)}
            </div>
          </div>
        </div>
      </div>
      
      {/* Teams Table */}
      <div className="card overflow-hidden">
        <div className="p-4 bg-gradient-to-r from-gray-50 to-gray-100 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-800">联赛排名</h2>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b-2 border-gray-200">
              <tr>
                <th className="px-6 py-4 text-left">
                  <button
                    onClick={() => handleSort('overall_rank')}
                    className="flex items-center space-x-1 font-semibold text-gray-700 hover:text-primary-600"
                  >
                    <span>Roto总排名</span>
                    {sortField === 'overall_rank' && (
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
                <th className="px-6 py-4 text-center font-semibold text-gray-700">战绩</th>
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
              {sortedTeams.map((team) => {
                const overallMedal = getMedal(team.overall_rank)
                const leagueMedal = getMedal(team.league_rank)
                
                return (
                  <tr key={team.team_key} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center space-x-2">
                        {overallMedal && <span className="text-xl">{overallMedal}</span>}
                        <span className={`font-bold ${overallMedal ? 'text-gradient text-lg' : 'text-gray-700'}`}>
                          #{team.overall_rank}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center space-x-2">
                        {leagueMedal && <span className="text-xl">{leagueMedal}</span>}
                        <span className="inline-flex items-center justify-center min-w-[2rem] h-8 px-3 rounded-full bg-blue-100 text-blue-800 font-semibold">
                          {team.league_rank || '-'}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="font-semibold text-gray-800">{team.team_name}</div>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <span className="inline-flex items-center px-3 py-1 rounded-full bg-gray-100 text-gray-800 font-semibold text-sm">
                        {team.wins || 0}-{team.losses || 0}-{team.ties || 0}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <span className="font-bold text-lg text-primary-600">
                        {team.total_roto_points.toFixed(2)}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <span className={`font-semibold ${
                        parseFloat(team.games_back) === 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {team.games_back}
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
      
      {/* Team Detail Modal */}
      {showModal && selectedTeam && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-gradient-to-r from-primary-500 to-secondary-500 text-white p-6 rounded-t-2xl">
              <div className="flex justify-between items-start">
                <div>
                  <h2 className="text-2xl font-bold mb-1">{selectedTeam.team_name}</h2>
                  <p className="text-white/90">经理: {selectedTeam.manager}</p>
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
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <div className="bg-gradient-to-br from-yellow-50 to-orange-50 p-4 rounded-xl border border-yellow-200">
                  <div className="text-sm text-gray-600 mb-1">Overall排名</div>
                  <div className="text-3xl font-bold text-gradient">#{selectedTeam.overall_rank}</div>
                </div>
                <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-4 rounded-xl border border-blue-200">
                  <div className="text-sm text-gray-600 mb-1">联赛排名</div>
                  <div className="text-3xl font-bold text-blue-600">#{selectedTeam.league_rank}</div>
                </div>
                <div className="bg-gradient-to-br from-green-50 to-teal-50 p-4 rounded-xl border border-green-200">
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
                <h3 className="text-lg font-bold text-gray-800 mb-3">联赛位置</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-gray-600">Games Back</div>
                    <div className={`text-2xl font-bold ${
                      parseFloat(selectedTeam.games_back) === 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {selectedTeam.games_back}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600">联赛排名</div>
                    <div className="text-2xl font-bold text-blue-600">
                      #{selectedTeam.league_rank}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default LeagueDetailPage
