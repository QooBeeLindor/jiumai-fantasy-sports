import { Link, useLocation } from 'react-router-dom'
import { Trophy, BarChart3, Github } from 'lucide-react'

const Layout = ({ children }) => {
  const location = useLocation()
  
  const isActive = (path) => {
    return location.pathname === path
  }
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Navigation */}
      <nav className="bg-white/80 backdrop-blur-md shadow-soft sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <Link to="/" className="flex items-center space-x-3 group">
              <div className="w-12 h-12 rounded-lg overflow-hidden group-hover:scale-110 transition-transform duration-300">
                <img src={`${import.meta.env.BASE_URL}jiumai-logo.jpg`} alt="九麦联赛LOGO" className="w-full h-full object-cover" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gradient">九麦NBA蛇形选秀联赛</h1>
                <p className="text-xs text-gray-500">Overall Roto Rankings</p>
              </div>
            </Link>
            
            {/* Navigation Links */}
            <div className="flex space-x-2">
              <Link
                to="/"
                className={`px-4 py-2 rounded-lg font-medium transition-all duration-300 ${
                  isActive('/')
                    ? 'bg-gradient-to-r from-primary-500 to-secondary-500 text-white shadow-md'
                    : 'text-gray-600 hover:text-primary-600 hover:bg-gray-100'
                }`}
              >
                首页
              </Link>
              <Link
                to="/overall-roto"
                className={`px-4 py-2 rounded-lg font-medium transition-all duration-300 ${
                  isActive('/overall-roto')
                    ? 'bg-gradient-to-r from-primary-500 to-secondary-500 text-white shadow-md'
                    : 'text-gray-600 hover:text-primary-600 hover:bg-gray-100'
                }`}
              >
                Overall Roto
              </Link>
              <Link
                to="/leagues"
                className={`px-4 py-2 rounded-lg font-medium transition-all duration-300 ${
                  location.pathname.startsWith('/league')
                    ? 'bg-gradient-to-r from-primary-500 to-secondary-500 text-white shadow-md'
                    : 'text-gray-600 hover:text-primary-600 hover:bg-gray-100'
                }`}
              >
                分盟排名
              </Link>
              <Link
                to="/adp"
                className={`px-4 py-2 rounded-lg font-medium transition-all duration-300 ${
                  isActive('/adp')
                    ? 'bg-gradient-to-r from-primary-500 to-secondary-500 text-white shadow-md'
                    : 'text-gray-600 hover:text-primary-600 hover:bg-gray-100'
                }`}
              >
                ADP
              </Link>
              <Link
                to="/fa-rankings"
                className={`px-4 py-2 rounded-lg font-medium transition-all duration-300 ${
                  isActive('/fa-rankings')
                    ? 'bg-gradient-to-r from-primary-500 to-secondary-500 text-white shadow-md'
                    : 'text-gray-600 hover:text-primary-600 hover:bg-gray-100'
                }`}
              >
                FA排行
              </Link>
              <Link
                to="/schedule"
                className={`px-4 py-2 rounded-lg font-medium transition-all duration-300 ${
                  isActive('/schedule')
                    ? 'bg-gradient-to-r from-primary-500 to-secondary-500 text-white shadow-md'
                    : 'text-gray-600 hover:text-primary-600 hover:bg-gray-100'
                }`}
              >
                赛程
              </Link>
            </div>
          </div>
        </div>
      </nav>
      
      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
      
      {/* Footer */}
      <footer className="bg-white/50 backdrop-blur-sm border-t border-gray-200 mt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
            <div className="text-center md:text-left">
              <p className="text-gray-600 font-medium">NBA Draft League - Overall Roto System</p>
              <p className="text-sm text-gray-500 mt-1">
                跨12个联赛的综合Roto积分排名系统
              </p>
            </div>
            
            <div className="flex items-center space-x-6">
              <div className="text-sm text-gray-500">
                <span className="font-medium">数据范围：</span> 2025-2026赛季
              </div>
              <a
                href="https://github.com"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center space-x-2 text-gray-600 hover:text-primary-600 transition-colors"
              >
                <Github className="w-5 h-5" />
                <span className="text-sm font-medium">GitHub</span>
              </a>
            </div>
          </div>
          
          <div className="mt-6 pt-6 border-t border-gray-200 text-center text-sm text-gray-500">
            Made with ❤️ for NBA Fantasy Basketball
          </div>
        </div>
      </footer>
    </div>
  )
}

export default Layout
