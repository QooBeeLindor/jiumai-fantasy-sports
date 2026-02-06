import { useState, useEffect } from 'react'
import { Search, Filter, TrendingUp, TrendingDown } from 'lucide-react'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5001'

const FARankingsPage = () => {
  const [players, setPlayers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  
  const [period, setPeriod] = useState('all')
  const [sortBy, setSortBy] = useState('net')
  const [limit, setLimit] = useState(100)
  
  useEffect(() => {
    fetchData()
  }, [period, sortBy, limit])
  
  const fetchData = async () => {
    try {
      setLoading(true)
      const params = { period, sort: sortBy, limit }
      
      const response = await axios.get(`${API_URL}/api/fa/rankings`, { params })
      setPlayers(response.data.data || [])
    } catch (err) {
      setError('加载数据失败')
    } finally {
      setLoading(false)
    }
  }
  
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
          <TrendingUp className="w-8 h-8 text-primary-500" />
          <div>
            <h1 className="text-3xl font-bold text-gray-800">FA Rankings</h1>
            <p className="text-gray-600 mt-1">Free Agent 交易排行榜</p>
          </div>
        </div>
      </div>
      
      <div className="card p-6 space-y-4">
        <div className="flex items-center space-x-2 mb-2">
          <Filter className="w-5 h-5 text-gray-700" />
          <span className="font-semibold text-gray-700">筛选</span>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
          >
            <option value="all">所有时间</option>
            <option value="week">最近一周</option>
            <option value="month">最近一月</option>
          </select>
          
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
          >
            <option value="net">净增加</option>
            <option value="adds">添加次数</option>
            <option value="drops">放弃次数</option>
          </select>
          
          <select
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
          >
            <option value={50}>前50名</option>
            <option value={100}>前100名</option>
            <option value={200}>全部显示</option>
          </select>
        </div>
        
        <div className="text-sm text-gray-500">
          显示 <span className="font-semibold text-primary-600">{players.length}</span> 名球员
        </div>
      </div>
      
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gradient-to-r from-gray-50 to-gray-100 border-b-2 border-gray-200">
              <tr>
                <th className="px-6 py-4 text-left font-semibold text-gray-700">排名</th>
                <th className="px-6 py-4 text-left font-semibold text-gray-700">球员</th>
                <th className="px-6 py-4 text-center font-semibold text-gray-700">Add</th>
                <th className="px-6 py-4 text-center font-semibold text-gray-700">Drop</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {players.map((player) => (
                <tr key={player.rank} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4">
                    <span className="text-lg font-bold text-gray-700">#{player.rank}</span>
                  </td>
                  <td className="px-6 py-4">
                    <span className="font-semibold text-gray-800">{player.player_name}</span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className="font-semibold text-green-600 text-lg">{player.add_count}</span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className="font-semibold text-red-600 text-lg">{player.drop_count}</span>
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

export default FARankingsPage
