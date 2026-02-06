import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import HomePage from './pages/HomePage'
import OverallRotoPage from './pages/OverallRotoPage'
import LeagueDetailPage from './pages/LeagueDetailPage'
import LeagueListPage from './pages/LeagueListPage'
import ADPPage from './pages/ADPPage'
import FARankingsPage from './pages/FARankingsPage'
import SchedulePage from './pages/SchedulePage'

function App() {
  return (
    <Router basename="/NBA/draftleague">  {/* ⭐ 添加这个！子目录路径 */}
      <Layout>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/overall-roto" element={<OverallRotoPage />} />
          <Route path="/league/:leagueId" element={<LeagueDetailPage />} />
          <Route path="/leagues" element={<LeagueListPage />} />
          <Route path="/adp" element={<ADPPage />} />
          <Route path="/fa-rankings" element={<FARankingsPage />} />
          <Route path="/schedule" element={<SchedulePage />} />
        </Routes>
      </Layout>
    </Router>
  )
}

export default App
