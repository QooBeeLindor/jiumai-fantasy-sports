import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5003'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Overall Roto Rankings API
export const getOverallRotoRankings = async (params = {}) => {
  const response = await api.get('/api/overall_roto/rankings', { params })
  return response.data
}

export const getOverallRotoTeam = async (teamKey) => {
  const response = await api.get(`/api/overall_roto/team/${teamKey}`)
  return response.data
}

export const getOverallRotoLeagues = async () => {
  const response = await api.get('/api/overall_roto/leagues')
  return response.data
}

export const getOverallRotoStats = async () => {
  const response = await api.get('/api/overall_roto/stats')
  return response.data
}

// League Detail API
export const getLeagueDetail = async (leagueId) => {
  const response = await api.get(`/api/league/${leagueId}/detail`)
  return response.data
}

// League Standings API
export const getAllLeagueStandings = async () => {
  const response = await api.get('/api/league_standings')
  return response.data
}

// Health Check
export const healthCheck = async () => {
  const response = await api.get('/api/health')
  return response.data
}

export default api
