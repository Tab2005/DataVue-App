import { motion } from 'framer-motion';
import { Users, TrendingUp, Zap, BarChart3 } from 'lucide-react';

const audiences = [
  {
    icon: BarChart3,
    title: '數據驅動行銷人',
    description: '每日與 Facebook Ads、GSC、GA4 為伍，深知數據價值的行銷從業人員。',
    highlight: '告別手動報表，專注策略制定',
    color: 'cyan'
  },
  {
    icon: TrendingUp,
    title: '成長型電商',
    description: '同時營運多平台的電商賣家，需要統一視角掌握全局效率。',
    highlight: '一站式掌握所有廣告與流量',
    color: 'purple'
  },
  {
    icon: Users,
    title: '數位代理商',
    description: '為客戶管理多個帳戶，需要快速產出洞察報告的專業團隊。',
    highlight: 'AI 輔助，半小時完成日報告',
    color: 'blue'
  },
  {
    icon: Zap,
    title: '獨立創作者',
    description: '自媒體與創作者，利用數據優化內容策略，最大化觸及與轉換。',
    highlight: '用數據指引創作方向',
    color: 'green'
  }
];

const colorMap = {
  cyan: { from: 'from-cyan-500', to: 'to-blue-500', text: 'text-cyan-400', border: 'border-cyan-500/20', glow: 'hover:shadow-cyan-500/10' },
  purple: { from: 'from-purple-500', to: 'to-pink-500', text: 'text-purple-400', border: 'border-purple-500/20', glow: 'hover:shadow-purple-500/10' },
  blue: { from: 'from-blue-500', to: 'to-indigo-500', text: 'text-blue-400', border: 'border-blue-500/20', glow: 'hover:shadow-blue-500/10' },
  green: { from: 'from-green-500', to: 'to-teal-500', text: 'text-green-400', border: 'border-green-500/20', glow: 'hover:shadow-green-500/10' }
};

export default function Audience() {
  return (
    <section id="audience" className="relative py-32 px-6 overflow-hidden">
      {/* 背景裝飾 */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-slate-900/30 to-transparent" />

      <div className="max-w-7xl mx-auto relative z-10">
        {/* 標題區 */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
          className="text-center mb-16"
        >
          <div className="status-tag mx-auto mb-6">
            <Users className="w-3.5 h-3.5 text-purple-400" />
            <span>適用場景</span>
          </div>
          <h2 className="section-title mb-4">
            為誰而生
            <br />
            <span className="gradient-text">為增長而設計</span>
          </h2>
          <p className="section-subtitle max-w-2xl mx-auto">
            無論你是獨行俠還是團隊作戰，DataVue 都能成為你的數據作戰中心。
          </p>
        </motion.div>

        {/* 受眾卡片網格 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {audiences.map((audience, index) => {
            const colors = colorMap[audience.color];
            return (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                whileHover={{ y: -8, transition: { duration: 0.3 } }}
                className={`
                  group relative rounded-2xl border border-white/5
                  bg-slate-900/40 backdrop-blur-sm p-6
                  hover:border-cyan-500/20 transition-all duration-500
                  hover:shadow-2xl ${colors.glow}
                `}
              >
                {/* 懸停光暈 */}
                <div className={`absolute inset-0 bg-gradient-to-br ${colors.from} to-transparent rounded-2xl opacity-0 group-hover:opacity-10 transition-opacity duration-500`} />

                <div className="relative z-10">
                  {/* 圖標 */}
                  <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${colors.from} ${colors.to} border border-white/10 flex items-center justify-center mb-5 group-hover:scale-110 transition-transform duration-300`}>
                    <audience.icon className="w-5 h-5 text-white" />
                  </div>

                  {/* 標題 */}
                  <h3 className="text-base font-semibold text-white mb-3">
                    {audience.title}
                  </h3>

                  {/* 描述 */}
                  <p className="text-sm text-slate-500 leading-relaxed mb-4">
                    {audience.description}
                  </p>

                  {/* 高亮標籤 */}
                  <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-gradient-to-r ${colors.from}/10 border ${colors.border}`}>
                    <span className={`w-1.5 h-1.5 rounded-full ${colors.text} animate-pulse`} />
                    <span className={`text-xs ${colors.text} font-medium`}>{audience.highlight}</span>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}