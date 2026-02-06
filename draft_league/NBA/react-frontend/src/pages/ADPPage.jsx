import { useState, useEffect } from 'react'
import { Search, Filter, Trophy, TrendingUp } from 'lucide-react'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5001'

const ADPPage = () => {
  const [players, setPlayers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  
  const [searchTerm, setSearchTerm] = useState('')
  const [positionFilter, setPositionFilter] = useState('')
  const [limit, setLimit] = useState(250)
  
  useEffect(() => {
    fetchData()
  }, [positionFilter, limit])
  
  const fetchData = async () => {
    try {
      setLoading(true)
      const params = { limit }
      if (positionFilter) {
        params.position = positionFilter
      }
      
      const response = await axios.get(`${API_URL}/api/adp/rankings`, { params })
      setPlayers(response.data.data || [])
    } catch (err) {
      setError('加载数据失败')
    } finally {
      setLoading(false)
    }
  }
  
  const filteredPlayers = players.filter(player => {
    const matchesSearch = player.player_name.toLowerCase().includes(searchTerm.toLowerCase())
    return matchesSearch
  })
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-16 h-16 border-4 border-primary-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    )
  }
  
  if (error) {
    return (
      <div className="card p-8 text-center">
        <p className="text-red-500">{error}</p>
        <button onClick={fetchData} className="btn btn-primary mt-4">重试</button>
      </div>
    )
  }
  
  return (
    <div className="space-y-6">
      <div className="card p-6">
        <div className="flex items-center space-x-4">
          <Trophy className="w-8 h-8 text-primary-500" />
          <div>
            <h1 className="text-3xl font-bold text-gray-800">ADP Rankings</h1>
            <p className="text-gray-600 mt-1">Average Draft Position - 平均选秀顺位</p>
          </div>
        </div>
      </div>
      
      <div className="card p-6 space-y-4">
        <div className="flex items-center space-x-2 mb-2">
          <Filter className="w-5 h-5 text-gray-700" />
          <span className="font-semibold text-gray-700">筛选</span>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="搜索球员..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
            />
          </div>
          
          <select
            value={positionFilter}
            onChange={(e) => setPositionFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
          >
            <option value="">所有位置</option>
            <option value="PG">PG</option>
            <option value="SG">SG</option>
            <option value="SF">SF</option>
            <option value="PF">PF</option>
            <option value="C">C</option>
          </select>
          
          <select
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
          >
            <option value={50}>前50名</option>
            <option value={100}>前100名</option>
            <option value={250}>全部显示</option>
          </select>
        </div>
        
        <div className="text-sm text-gray-500">
          显示 <span className="font-semibold text-primary-600">{filteredPlayers.length}</span> 名球员
        </div>
      </div>
      
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gradient-to-r from-gray-50 to-gray-100 border-b-2 border-gray-200">
              <tr>
                <th className="px-6 py-4 text-left font-semibold text-gray-700">ADP</th>
                <th className="px-6 py-4 text-left font-semibold text-gray-700">球员</th>
                <th className="px-6 py-4 text-left font-semibold text-gray-700">位置</th>
                <th className="px-6 py-4 text-left font-semibold text-gray-700">球队</th>
                <th className="px-6 py-4 text-center font-semibold text-gray-700">被选次数</th>
                <th className="px-6 py-4 text-center font-semibold text-gray-700">最高顺位</th>
                <th className="px-6 py-4 text-center font-semibold text-gray-700">最低顺位</th>
                <th className="px-6 py-4 text-center font-semibold text-gray-700">选中率</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {filteredPlayers.map((player) => (
                <tr key={player.player_id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4">
                    <span className="text-lg font-bold text-primary-600">
                      {player.adp.toFixed(1)}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className="font-semibold text-gray-800">{player.player_name}</span>
                  </td>
                  <td className="px-6 py-4">
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      {player.position}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-gray-600">{player.team}</td>
                  <td className="px-6 py-4 text-center text-gray-700">{player.times_drafted}</td>
                  <td className="px-6 py-4 text-center text-green-600 font-semibold">{player.min_pick}</td>
                  <td className="px-6 py-4 text-center text-red-600 font-semibold">{player.max_pick}</td>
                  <td className="px-6 py-4 text-center">
                    <span className="font-semibold text-gray-700">{player.drafted_percentage}%</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default ADPPage
