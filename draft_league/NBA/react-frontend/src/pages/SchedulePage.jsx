import { useState, useEffect } from 'react'
import { Calendar, ChevronLeft, ChevronRight, Filter } from 'lucide-react'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5001'

const SchedulePage = () => {
  const [weeks, setWeeks] = useState([])
  const [currentWeek, setCurrentWeek] = useState(null)
  const [weekData, setWeekData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [leagueFilter, setLeagueFilter] = useState('')
  
  useEffect(() => {
    fetchWeeks()
  }, [])
  
  useEffect(() => {
    if (currentWeek) {
      fetchWeekData()
    }
  }, [currentWeek, leagueFilter])
  
  const fetchWeeks = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/schedule/weeks`)
      const weekList = response.data.data || []
      setWeeks(weekList)
      if (weekList.length > 0) {
        setCurrentWeek(weekList[weekList.length - 1]) // 最新一周
      }
    } catch (err) {
      setError('加载周列表失败')
    }
  }
  
  const fetchWeekData = async () => {
    try {
      setLoading(true)
      const params = leagueFilter ? { league_id: leagueFilter } : {}
      const response = await axios.get(`${API_URL}/api/schedule/week/${currentWeek}`, { params })
      setWeekData(response.data.data)
    } catch (err) {
      setError('加载赛程数据失败')
    } finally {
      setLoading(false)
    }
  }
  
  const goToPreviousWeek = () => {
    const currentIndex = weeks.indexOf(currentWeek)
    if (currentIndex > 0) {
      setCurrentWeek(weeks[currentIndex - 1])
    }
  }
  
  const goToNextWeek = () => {
    const currentIndex = weeks.indexOf(currentWeek)
    if (currentIndex < weeks.length - 1) {
      setCurrentWeek(weeks[currentIndex + 1])
    }
  }
  
  if (loading && !weekData) {
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
        <button onClick={fetchWeeks} className="btn btn-primary mt-4">重试</button>
      </div>
    )
  }
  
  return (
    <div className="space-y-6">
      <div className="card p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Calendar className="w-8 h-8 text-primary-500" />
            <div>
              <h1 className="text-3xl font-bold text-gray-800">赛程日历</h1>
              <p className="text-gray-600 mt-1">查看每周比赛安排</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <button
              onClick={goToPreviousWeek}
              disabled={weeks.indexOf(currentWeek) === 0}
              className="p-2 rounded-lg hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-6 h-6" />
            </button>
            
            <div className="text-center">
              <div className="text-2xl font-bold text-primary-600">Week {currentWeek}</div>
              <div className="text-sm text-gray-500">第{currentWeek}周</div>
            </div>
            
            <button
              onClick={goToNextWeek}
              disabled={weeks.indexOf(currentWeek) === weeks.length - 1}
              className="p-2 rounded-lg hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronRight className="w-6 h-6" />
            </button>
          </div>
        </div>
      </div>
      
      {weekData && (
        <div className="space-y-6">
          {weekData.leagues.map((league) => (
            <div key={league.league_id} className="card overflow-hidden">
              <div className="bg-gradient-to-r from-primary-500 to-secondary-500 text-white p-4">
                <h2 className="text-xl font-bold">{league.league_name}</h2>
                <p className="text-sm text-white/80">Tier {league.tier}</p>
              </div>
              
              <div className="p-4">
                <div className="space-y-3">
                  {league.matches.map((match) => {
                    const isPlayer1Winner = match.winner === 1
                    const isPlayer2Winner = match.winner === 2
                    const isTie = match.winner === 0
                    
                    return (
                      <div
                        key={match.match_id}
                        className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                      >
                        <div className="flex-1 text-right">
                          <span className={`font-semibold ${isPlayer1Winner ? 'text-green-600' : 'text-gray-700'}`}>
                            {match.player1_name}
                          </span>
                        </div>
                        
                        <div className="px-6 text-center">
                          <div className="flex items-center space-x-3">
                            <span className={`text-xl font-bold ${isPlayer1Winner ? 'text-green-600' : 'text-gray-600'}`}>
                              {match.score1}
                            </span>
                            <span className="text-gray-400">vs</span>
                            <span className={`text-xl font-bold ${isPlayer2Winner ? 'text-green-600' : 'text-gray-600'}`}>
                              {match.score2}
                            </span>
                          </div>
                          {isTie && (
                            <span className="text-xs text-gray-500 mt-1 inline-block">平局</span>
                          )}
                        </div>
                        
                        <div className="flex-1 text-left">
                          <span className={`font-semibold ${isPlayer2Winner ? 'text-green-600' : 'text-gray-700'}`}>
                            {match.player2_name}
                          </span>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default SchedulePage
