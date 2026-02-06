import { Link } from 'react-router-dom'
import { Trophy, BarChart3, TrendingUp, Users, ArrowRight } from 'lucide-react'

const HomePage = () => {
  const features = [
    {
      icon: Trophy,
      title: 'Overall Roto Rankings',
      description: '跨12个联赛的综合Roto积分排名，公平对比所有球队实力',
      link: '/overall-roto',
      color: 'from-yellow-400 to-orange-500'
    },
    {
      icon: BarChart3,
      title: '分盟详细排名',
      description: '查看每个联赛内的详细排名，包含Games Back和各项数据',
      link: '/leagues',
      color: 'from-blue-400 to-indigo-500'
    },
    {
      icon: TrendingUp,
      title: 'ADP Rankings',
      description: 'Average Draft Position - 平均选秀顺位排名',
      link: '/adp',
      color: 'from-green-400 to-teal-500'
    },
    {
      icon: Users,
      title: 'FA Rankings',
      description: 'Free Agent交易排行榜，查看热门球员动态',
      link: '/fa-rankings',
      color: 'from-purple-400 to-pink-500'
    },
    {
      icon: TrendingUp,
      title: '赛程日历',
      description: '查看每周比赛安排和结果',
      link: '/schedule',
      color: 'from-red-400 to-pink-500'
    },
    {
      icon: BarChart3,
      title: '数据中心',
      description: '综合数据分析和统计信息',
      link: '/overall-roto',
      color: 'from-indigo-400 to-purple-500'
    }
  ]
  
  const stats = [
    { label: '联赛数量', value: '12', unit: '个' },
    { label: '球队总数', value: '192', unit: '支' },
    { label: 'Stat类别', value: '11', unit: '项' }
  ]
  
  return (
    <div className="space-y-16">
      {/* Hero Section */}
      <section className="text-center space-y-8 py-12">
        <div className="inline-flex items-center justify-center w-32 h-32 rounded-2xl shadow-hard mb-6 overflow-hidden">
          <img src={`${import.meta.env.BASE_URL}jiumai-logo.jpg`} alt="九麦联赛LOGO" className="w-full h-full object-cover" />
        </div>
        
        <h1 className="text-5xl md:text-6xl font-bold">
          <span className="text-gradient">九麦NBA蛇形选秀联赛</span>
          <br />
          <span className="text-gray-700 text-3xl md:text-4xl mt-2 block">
            Overall Roto Rankings System
          </span>
        </h1>
        
        <p className="text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
          跨越12个NBA范特西联赛的综合排名系统，基于Roto积分计算，
          <br />
          结合真实联赛排名数据，全面展现球队实力
        </p>
        
        <div className="flex justify-center gap-4 mt-8">
          <Link
            to="/overall-roto"
            className="btn btn-primary text-lg px-8 py-3 flex items-center space-x-2"
          >
            <span>查看总排名</span>
            <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </section>
      
      {/* Stats Section */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {stats.map((stat, index) => (
          <div
            key={index}
            className="card p-6 text-center hover:-translate-y-1 transition-transform duration-300"
          >
            <div className="text-4xl font-bold text-gradient mb-2">
              {stat.value}
            </div>
            <div className="text-gray-600 font-medium">
              {stat.label}
              {stat.unit && <span className="text-gray-400 ml-1">{stat.unit}</span>}
            </div>
          </div>
        ))}
      </section>
      
      {/* Features Section */}
      <section className="space-y-8">
        <div className="text-center">
          <h2 className="text-3xl font-bold text-gray-800 mb-3">核心功能</h2>
          <p className="text-gray-600">探索系统的强大功能</p>
        </div>
        
        <div className="grid md:grid-cols-2 gap-6">
          {features.map((feature, index) => (
            <Link
              key={index}
              to={feature.link}
              className="card p-8 hover:-translate-y-1 transition-all duration-300 group"
            >
              <div className={`inline-flex items-center justify-center w-14 h-14 bg-gradient-to-br ${feature.color} rounded-xl shadow-md mb-4 group-hover:scale-110 transition-transform duration-300`}>
                <feature.icon className="w-7 h-7 text-white" />
              </div>
              
              <h3 className="text-xl font-bold text-gray-800 mb-2 group-hover:text-primary-600 transition-colors">
                {feature.title}
              </h3>
              
              <p className="text-gray-600 leading-relaxed">
                {feature.description}
              </p>
              
              <div className="mt-4 flex items-center text-primary-600 font-medium group-hover:translate-x-2 transition-transform duration-300">
                <span>了解更多</span>
                <ArrowRight className="w-4 h-4 ml-2" />
              </div>
            </Link>
          ))}
        </div>
      </section>
      
      {/* How it Works Section */}
      <section className="bg-white/50 backdrop-blur-sm rounded-2xl p-8 md:p-12 shadow-soft">
        <h2 className="text-3xl font-bold text-gray-800 mb-8 text-center">工作原理</h2>
        
        <div className="space-y-6 max-w-3xl mx-auto">
          <div className="flex items-start space-x-4">
            <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-primary-500 to-secondary-500 rounded-full flex items-center justify-center text-white font-bold shadow-md">
              1
            </div>
            <div>
              <h3 className="text-lg font-bold text-gray-800 mb-1">数据采集</h3>
              <p className="text-gray-600">从Yahoo Fantasy Basketball API获取12个联赛的实时数据</p>
            </div>
          </div>
          
          <div className="flex items-start space-x-4">
            <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-primary-500 to-secondary-500 rounded-full flex items-center justify-center text-white font-bold shadow-md">
              2
            </div>
            <div>
              <h3 className="text-lg font-bold text-gray-800 mb-1">Roto积分计算</h3>
              <p className="text-gray-600">基于11个stat类别（FG%、FT%、3PM等）计算每支球队的Roto积分</p>
            </div>
          </div>
          
          <div className="flex items-start space-x-4">
            <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-primary-500 to-secondary-500 rounded-full flex items-center justify-center text-white font-bold shadow-md">
              3
            </div>
            <div>
              <h3 className="text-lg font-bold text-gray-800 mb-1">综合排名</h3>
              <p className="text-gray-600">汇总所有联赛数据，生成跨联赛的Overall排名</p>
            </div>
          </div>
          
          <div className="flex items-start space-x-4">
            <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-primary-500 to-secondary-500 rounded-full flex items-center justify-center text-white font-bold shadow-md">
              4
            </div>
            <div>
              <h3 className="text-lg font-bold text-gray-800 mb-1">可视化展示</h3>
              <p className="text-gray-600">通过直观的表格和图表展示排名，支持搜索、筛选和排序</p>
            </div>
          </div>
        </div>
      </section>
      
      {/* CTA Section */}
      <section className="text-center py-12 bg-gradient-to-r from-primary-500 to-secondary-500 rounded-2xl shadow-hard text-white">
        <h2 className="text-3xl font-bold mb-4">准备好探索排名了吗？</h2>
        <p className="text-xl mb-8 opacity-90">查看192支球队的综合实力排名</p>
        <Link
          to="/overall-roto"
          className="inline-flex items-center space-x-2 bg-white text-primary-600 px-8 py-3 rounded-lg font-bold text-lg hover:shadow-2xl hover:-translate-y-1 transition-all duration-300"
        >
          <Trophy className="w-5 h-5" />
          <span>进入排名系统</span>
        </Link>
      </section>
    </div>
  )
}

export default HomePage
