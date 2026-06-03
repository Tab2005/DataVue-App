import { motion } from 'framer-motion';
import { Link2, Sparkles, Zap, KeyRound, Workflow, Share2 } from 'lucide-react';

const steps = [
  {
    num: "01",
    icon: <KeyRound className="w-5 h-5 text-brand-blue" />,
    title: "Connect (一鍵串接)",
    subTitle: "OAuth2 Secure Protocol",
    description: "透過安全的 Google 與 Facebook 官方授權協議，點擊即可完成對接。我們採用加密的 Fernet Token 儲存機制，確保您的資產安全無虞。",
    glow: "rgba(59, 130, 246, 0.15)"
  },
  {
    num: "02",
    icon: <Workflow className="w-5 h-5 text-brand-purple" />,
    title: "Synthesize (智能熔煉)",
    subTitle: "AI Modeling & Processing",
    description: "系統自動執行多源數據的清洗、去噪與關聯性建模。GA4 事件路徑、FB 競價重疊與 GSC 關鍵字，在這一階段被對齊成單一視圖。",
    glow: "rgba(139, 92, 246, 0.15)"
  },
  {
    num: "03",
    icon: <Share2 className="w-5 h-5 text-brand-cyan" />,
    title: "Accelerate (戰略躍遷)",
    subTitle: "AI Studio Strategic Output",
    description: "開啟 AI 戰略協作。獲取每週數據解譯與具體可執行的優化計畫，不再面對冰冷數字手足無措，以極速反應搶佔市場先機。",
    glow: "rgba(6, 182, 212, 0.15)"
  }
];

export default function HowItWorks() {
  return (
    <section id="how-it-works" className="py-32 px-6 relative overflow-hidden bg-black/10">
      {/* 背景裝飾 */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[250px] bg-brand-cyan/[0.01] rounded-full blur-[140px] pointer-events-none" />

      <div className="max-w-7xl mx-auto relative z-10">
        {/* 標題 */}
        <div className="text-center mb-24">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-white/5 bg-[#0a0c10]/40 backdrop-blur-md mb-6">
            <Workflow className="w-3.5 h-3.5 text-brand-cyan" />
            <span className="text-[10px] font-display font-medium tracking-widest text-slate-400 uppercase">THE ENGAGEMENT BLUEPRINT</span>
          </div>
          
          <h2 className="text-3xl md:text-5xl font-sans font-bold mb-4 text-white">
            簡單三步，<span className="font-serif italic font-normal text-chrome-gradient">點燃數據</span>
          </h2>
          <p className="text-slate-500 max-w-xl mx-auto text-sm font-light">
            從數據混亂到決策清晰，只需幾分鐘的熔煉過程。
          </p>
        </div>

        {/* 步驟橫向編排與極細連線 */}
        <div className="relative">
          {/* 背景貫穿橫線 (Desktop) */}
          <div className="hidden md:block absolute top-1/2 left-16 right-16 h-[1px] bg-gradient-to-r from-brand-blue/30 via-brand-purple/30 to-brand-cyan/30 -translate-y-1/2 -z-10 opacity-30" />
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {steps.map((item, index) => (
              <motion.div 
                key={index}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-100px" }}
                transition={{ duration: 0.8, delay: index * 0.2, ease: [0.16, 1, 0.3, 1] }}
                className="group relative flex flex-col items-center text-center p-8 rounded-3xl border border-white/[0.03] bg-[#07090d]/30 backdrop-blur-sm transition-all duration-500 hover:bg-[#0b0e14]/50 hover:border-white/[0.06]"
              >
                {/* 步驟發光效果 */}
                <div 
                  className="absolute inset-0 rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 blur-xl pointer-events-none -z-10" 
                  style={{ background: `radial-gradient(circle, ${item.glow} 0%, transparent 70%)` }}
                />

                {/* 步驟編號 */}
                <div className="absolute top-4 right-6 font-display font-light text-slate-700 text-sm group-hover:text-slate-500 transition-colors duration-500">
                  {item.num}
                </div>

                {/* 核心圓環 (Reactor) */}
                <div className="w-16 h-16 rounded-full border border-white/5 bg-black flex items-center justify-center mb-8 relative group-hover:scale-105 transition-transform duration-500">
                  {/* 外層微弱動態光環 */}
                  <div className="absolute -inset-1 bg-gradient-to-tr from-brand-blue via-brand-purple to-brand-cyan rounded-full opacity-0 group-hover:opacity-30 transition-opacity duration-500 blur-sm" />
                  <div className="absolute inset-0.5 bg-black rounded-full flex items-center justify-center relative z-10 border border-white/5">
                    {item.icon}
                  </div>
                </div>

                <h3 className="text-lg font-semibold text-white mb-2 tracking-wide">
                  {item.title}
                </h3>
                <span className="text-[9px] font-display text-slate-500 tracking-wider uppercase mb-4 block">
                  {item.subTitle}
                </span>
                
                <p className="text-xs text-slate-400 leading-relaxed font-light">
                  {item.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
