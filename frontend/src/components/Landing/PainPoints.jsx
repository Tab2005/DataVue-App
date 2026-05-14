import { motion } from 'framer-motion';
import { FiXCircle, FiCheckCircle } from 'react-icons/fi';

const painPoints = [
  {
    icon: <FiXCircle className="w-10 h-10 text-red-500/70" />,
    solIcon: <FiCheckCircle className="w-10 h-10 text-brand-cyan" />,
    title: "報表分散",
    problem: "登入多個平台，每天在不同頁面切換，數據難以對齊。",
    solution: "一站式儀表板，跨平台數據即刻對照，一眼看穿局勢。"
  },
  {
    icon: <FiXCircle className="w-10 h-10 text-red-500/70" />,
    solIcon: <FiCheckCircle className="w-10 h-10 text-brand-purple" />,
    title: "分析盲點",
    problem: "看著滿滿的數字不知從何優化，甚至不知道哪裡出錯。",
    solution: "AI 戰略導向，深度剖析用戶意圖並提供具體行動建議。"
  },
  {
    icon: <FiXCircle className="w-10 h-10 text-red-500/70" />,
    solIcon: <FiCheckCircle className="w-10 h-10 text-brand-blue" />,
    title: "擴充困難",
    problem: "系統僵化，當需要串接新平台時往往束手無策。",
    solution: "模組化架構，如同套件般靈活。未來，我們與您共同成長。"
  }
];

export default function PainPoints() {
  return (
    <section id="solutions" className="py-24 px-6 bg-slate-950/20">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-5xl font-display font-bold mb-4">為什麼選擇 DataVue？</h2>
          <p className="text-slate-400 max-w-xl mx-auto">我們懂您的痛苦，因此我們打造了更聰明的解決方案。</p>
        </div>

        <div className="grid grid-cols-1 gap-8">
          {painPoints.map((item, index) => (
            <motion.div 
              key={index}
              initial={{ opacity: 0, x: index % 2 === 0 ? -20 : 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: index * 0.1 }}
              className="glass rounded-3xl p-8 border-white/5 flex flex-col md:flex-row gap-12 items-center"
            >
              <div className="flex-1 opacity-50 grayscale hover:grayscale-0 transition-all duration-500">
                <div className="flex items-start gap-4 mb-4">
                  {item.icon}
                  <div>
                    <h3 className="text-xl font-bold text-slate-300 mb-2">痛點</h3>
                    <p className="text-slate-400">{item.problem}</p>
                  </div>
                </div>
              </div>

              <div className="hidden md:block w-px h-24 bg-gradient-to-b from-transparent via-white/10 to-transparent" />

              <div className="flex-1 bg-gradient-to-br from-white/5 to-transparent p-6 rounded-2xl border border-white/10 group">
                <div className="flex items-start gap-4">
                  <div className="group-hover:scale-110 transition-transform">
                    {item.solIcon}
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-white mb-2">DataVue 解決方案</h3>
                    <p className="text-slate-200">{item.solution}</p>
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
