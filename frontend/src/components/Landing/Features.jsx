import { motion } from 'motion';
import { Search, Facebook, BarChart3, Bot } from 'lucide-react';

const features = [
  {
    icon: <Search className="w-8 h-8 text-blue-400" />,
    title: "GSC 搜尋意圖洞察",
    description: "深入關鍵字戰場，掌握受眾真實的搜尋動機與意圖，而不僅僅是排名。",
    color: "from-blue-500/20 to-transparent"
  },
  {
    icon: <Facebook className="w-8 h-8 text-cyan-400" />,
    title: "Facebook Ads 精準追蹤",
    description: "一目了然的廣告表現追蹤，實時優化轉化成本，拒絕預算浪費。",
    color: "from-cyan-500/20 to-transparent"
  },
  {
    icon: <BarChart3 className="w-8 h-8 text-purple-400" />,
    title: "GA4 全方位流量分析",
    description: "還原用戶網站行為路徑，進行深度的內容分組優化，提升跳出率表現。",
    color: "from-purple-500/20 to-transparent"
  },
  {
    icon: <Bot className="w-8 h-8 text-emerald-400" />,
    title: "Site-tegy AI Hub",
    description: "24小時 AI 分析師，整合多源數據，產出具備「勝負感」的具體優化指令。",
    color: "from-emerald-500/20 to-transparent"
  }
];

export default function Features() {
  return (
    <section id="features" className="py-24 px-6 relative overflow-hidden">
      {/* Decorative Orbs */}
      <div className="absolute top-1/2 left-0 w-64 h-64 bg-brand-blue/5 rounded-full blur-[100px]" />
      <div className="absolute bottom-0 right-0 w-64 h-64 bg-brand-purple/5 rounded-full blur-[100px]" />

      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-5xl font-display font-bold mb-4">核心功能</h2>
          <p className="text-slate-400 max-w-xl mx-auto">強大的模組化工具，為您的業務增長提供動力。</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature, index) => (
            <motion.div 
              key={index}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              whileHover={{ y: -10 }}
              className={`glass rounded-3xl p-8 border-white/5 relative overflow-hidden group bg-gradient-to-br ${feature.color}`}
            >
              <div className="mb-6 bg-white/5 w-16 h-16 rounded-2xl flex items-center justify-center border border-white/10 group-hover:scale-110 transition-transform duration-500">
                {feature.icon}
              </div>
              <h3 className="text-xl font-bold text-white mb-3">{feature.title}</h3>
              <p className="text-slate-400 text-sm leading-relaxed group-hover:text-slate-300 transition-colors">
                {feature.description}
              </p>
              
              {/* Corner Glow */}
              <div className="absolute -bottom-2 -right-2 w-12 h-12 bg-white/5 rounded-full blur-xl group-hover:bg-white/10 transition-colors" />
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
