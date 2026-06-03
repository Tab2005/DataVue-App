import { motion } from 'framer-motion';
import { User, Building, Rocket, Sparkles, TrendingUp, Cpu } from 'lucide-react';

const targets = [
  {
    icon: <User className="w-5 h-5 text-brand-blue" />,
    title: "個人品牌創作者",
    subTitle: "Solo Creators",
    description: "精準鎖定高價值內容。不再盲目跟風熱點，而是用 GSC 意圖分析挖掘用戶真實痛點，將流量高效轉化為訂閱與變現。",
    metric: "核心受眾黏著度",
    value: "+58%",
    glow: "group-hover:shadow-[0_0_40px_rgba(59,130,246,0.15)]"
  },
  {
    icon: <Building className="w-5 h-5 text-brand-purple" />,
    title: "增長型電商與品牌",
    subTitle: "Growth Brands",
    description: "最大化跨平台廣告效能。一站式比對 FB Ads ROAS 與 GA4 下單轉化，即時預警受眾重疊，避免在重複的人群中相互競價浪費預算。",
    metric: "行銷預算轉化效率",
    value: "+34%",
    glow: "group-hover:shadow-[0_0_40px_rgba(139,92,246,0.15)]"
  },
  {
    icon: <Rocket className="w-5 h-5 text-brand-cyan" />,
    title: "敏捷決策團隊",
    subTitle: "Agile Teams",
    description: "建立數據驅動的團隊文化。去除人工手動整理 Excel 的低效，以 AI 虛擬分析師主動推送數據洞察，大幅縮短戰術調整的反應時間。",
    metric: "報表彙整工時節省",
    value: "-82%",
    glow: "group-hover:shadow-[0_0_40px_rgba(6,118,246,0.15)]"
  }
];

export default function Audience() {
  return (
    <section id="target" className="py-32 px-6 bg-black/30 border-b border-white/[0.02] relative">
      <div className="absolute top-0 right-1/4 w-[1px] h-full bg-gradient-to-b from-white/5 via-transparent to-white/5 hidden lg:block" />

      <div className="max-w-7xl mx-auto relative z-10">
        {/* 標題 */}
        <div className="text-center mb-20">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-white/5 bg-[#0a0c10]/40 backdrop-blur-md mb-6">
            <Cpu className="w-3.5 h-3.5 text-brand-purple" />
            <span className="text-[10px] font-display font-medium tracking-widest text-slate-400 uppercase">TARGET COHORT SYMBIOSIS</span>
          </div>
          
          <h2 className="text-3xl md:text-5xl font-sans font-bold mb-4 text-white">
            與您共鳴的<span className="font-serif italic font-normal text-chrome-gradient">決策生態</span>
          </h2>
          <p className="text-slate-500 max-w-xl mx-auto text-sm font-light">
            無論是個人耕耘還是團隊作戰，DataVue 都能為您找到行銷增長的專屬軌跡。
          </p>
        </div>

        {/* 奢華精緻三欄卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {targets.map((item, index) => (
            <motion.div 
              key={index}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-100px" }}
              transition={{ duration: 0.8, delay: index * 0.15, ease: [0.16, 1, 0.3, 1] }}
              className={`group relative rounded-3xl border border-white/[0.03] bg-[#07090d]/30 backdrop-blur-md p-8 flex flex-col justify-between transition-all duration-500 hover:bg-[#0b0e14]/50 hover:border-white/[0.08] ${item.glow}`}
            >
              {/* 卡片頂部 */}
              <div>
                <div className="flex items-center justify-between mb-8">
                  <div className="w-10 h-10 rounded-xl bg-white/5 border border-white/5 flex items-center justify-center group-hover:scale-110 transition-transform duration-500">
                    {item.icon}
                  </div>
                  <span className="text-[10px] font-display font-medium tracking-widest text-slate-500 uppercase">
                    {item.subTitle}
                  </span>
                </div>

                <h3 className="text-lg font-semibold text-white mb-4 tracking-wide">
                  {item.title}
                </h3>
                
                <p className="text-xs text-slate-400 leading-relaxed font-light mb-12">
                  {item.description}
                </p>
              </div>

              {/* 卡片底部指標展示 (帶有微型動態圖表暗示) */}
              <div className="border-t border-white/[0.04] pt-6 relative overflow-hidden">
                <div className="flex justify-between items-end">
                  <div>
                    <span className="text-[9px] font-display text-slate-500 uppercase tracking-wider block mb-1">
                      {item.metric}
                    </span>
                    <span className="text-3xl font-display font-extrabold text-white tracking-tight">
                      {item.value}
                    </span>
                  </div>

                  {/* 迷你折線裝飾圖 */}
                  <div className="w-20 h-8 opacity-20 group-hover:opacity-40 transition-opacity duration-500">
                    <svg className="w-full h-full" viewBox="0 0 100 40">
                      <path 
                        d={index === 0 ? "M0,35 Q25,10 50,25 T100,5" : index === 1 ? "M0,30 Q25,25 50,15 T100,10" : "M0,38 Q25,30 50,12 T100,8"} 
                        fill="none" 
                        stroke="currentColor" 
                        strokeWidth="2"
                        className="text-white"
                      />
                    </svg>
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
