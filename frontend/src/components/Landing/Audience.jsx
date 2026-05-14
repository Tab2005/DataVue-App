import { motion } from 'framer-motion';
import { User, Building2, Rocket } from 'lucide-react';

const targets = [
  {
    icon: <User className="w-10 h-10 text-brand-blue" />,
    title: "個人品牌創作者",
    description: "精準掌控內容影響力，將粉絲轉化為忠誠客戶。"
  },
  {
    icon: <Building2 className="w-10 h-10 text-brand-purple" />,
    title: "中小企業 / 電商",
    description: "最大化跨平台廣告效益，降低獲客成本，提升 LTV。"
  },
  {
    icon: <Rocket className="w-10 h-10 text-brand-cyan" />,
    title: "初創團隊",
    description: "快速建立「數據驅動」的決策文化，避免盲目燒錢。"
  }
];

export default function Audience() {
  return (
    <section id="target" className="py-24 px-6 bg-slate-900/10">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-5xl font-display font-bold mb-4">適用對象</h2>
          <p className="text-slate-400 max-w-xl mx-auto">無論規模大小，DataVue 都能為您找到增長路徑。</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {targets.map((item, index) => (
            <motion.div 
              key={index}
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className="glass p-8 rounded-3xl border-white/5 text-center group hover:bg-white/[0.05] transition-all"
            >
              <div className="inline-flex mb-6 p-4 rounded-2xl bg-white/5 border border-white/10 group-hover:scale-110 transition-transform">
                {item.icon}
              </div>
              <h3 className="text-2xl font-bold text-white mb-4">{item.title}</h3>
              <p className="text-slate-400 leading-relaxed">{item.description}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
