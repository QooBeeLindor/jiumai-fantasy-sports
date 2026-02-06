import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Trophy, Users, ExternalLink } from 'lucide-react'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5001'

const LeagueListPage = () => {
  const [leagues, setLeagues] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  
  useEffect(() => {
    fetchData()
  }, [])
  
  const fetchData = async () => {
    try {
      setLoading(true)
      const response = await axios.get(`${API_URL}/api/overall_roto/leagues`)
      setLeagues(response.data.data || [])
    } catch (err) {
      setError('加载联赛列表失败')
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
          <Trophy className="w-8 h-8 text-primary-500" />
          <div>
            <h1 className="text-3xl font-bold text-gray-800">选择联赛</h1>
            <p className="text-gray-600 mt-1">查看各联赛详细排名信息</p>
          </div>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {leagues.map((league) => (
          <Link
            key={league.id}
            to={`/league/${league.id}`}
            className="card p-6 hover:-translate-y-1 hover:shadow-lg transition-all duration-300 group"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-gradient-to-br from-primary-500 to-secondary-500 rounded-lg shadow-md group-hover:scale-110 transition-transform">
                <Users className="w-6 h-6 text-white" />
              </div>
              <ExternalLink className="w-5 h-5 text-gray-400 group-hover:text-primary-600 transition-colors" />
            </div>
            
            <h3 className="text-xl font-bold text-gray-800 mb-2 group-hover:text-primary-600 transition-colors">
              {league.name}
            </h3>
            
            <div className="text-sm text-gray-500">
              联赛 ID: {league.id}
            </div>
          </Link>
        ))}
      </div>
      
      <div className="card p-6 bg-blue-50 border border-blue-200">
        <h3 className="font-bold text-gray-800 mb-2">💡 提示</h3>
        <p className="text-gray-600 text-sm">
          点击任意联赛卡片查看该联赛的详细排名信息，包括Overall排名、联赛内排名、Roto积分、Games Back等数据。
        </p>
      </div>
    </div>
  )
}

export default LeagueListPage
