import { motion } from 'framer-motion';
import { ArrowRight, Sparkles, Activity, ShieldAlert, BarChart } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function Hero() {
  const navigate = useNavigate();

  // 定義動態效果的 Framer Motion 變數
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.15,
        delayChildren: 0.2
      }
    }
  };

  const itemVariants = {
    hidden: { y: 30, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: { duration: 0.8, ease: [0.16, 1, 0.3, 1] }
    }
  };

  return (
    <section className="relative pt-40 pb-24 px-6 overflow-hidden min-h-screen flex flex-col items-center justify-center bg-mesh bg-grid">
      {/* 背景透視流光與極薄光暈 */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-gradient-to-tr from-brand-blue/5 via-brand-purple/5 to-brand-cyan/5 rounded-full blur-[160px] -z-10 pointer-events-none" />
      <div className="absolute -top-40 -left-40 w-96 h-96 bg-brand-cyan/[0.02] rounded-full blur-[100px] -z-10 pointer-events-none" />
      <div className="absolute bottom-10 right-10 w-[500px] h-[500px] bg-brand-purple/[0.02] rounded-full blur-[120px] -z-10 pointer-events-none" />

      {/* 細微的對稱機械對焦裝飾線 */}
      <div className="absolute left-10 top-1/2 -translate-y-1/2 w-[1px] h-32 bg-gradient-to-b from-transparent via-white/10 to-transparent hidden lg:block" />
      <div className="absolute right-10 top-1/2 -translate-y-1/2 w-[1px] h-32 bg-gradient-to-b from-transparent via-white/10 to-transparent hidden lg:block" />

      <div className="max-w-7xl mx-auto w-full grid grid-cols-1 lg:grid-cols-12 gap-16 items-center">
        {/* 左側：精美社論標題區 */}
        <motion.div 
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="lg:col-span-7 text-left flex flex-col items-start"
        >
          {/* 狀態標籤 - 極簡鋼鐵黑與微光 */}
          <motion.div 
            variants={itemVariants}
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-white/5 bg-[#0a0c10]/60 backdrop-blur-md mb-8"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-brand-cyan animate-pulse shadow-[0_0_8px_#06b6d4]" />
            <span className="text-[10px] font-display font-medium tracking-widest text-slate-400 uppercase">DataVue Engine v2.0 Live</span>
          </motion.div>
          
          {/* 標題 - 混合 Outfit (現代幾何) 與 Fraunces (極致襯線/斜體) */}
          <motion.h1 
            variants={itemVariants}
            className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold tracking-tight text-white leading-[1.1] mb-8 font-sans"
          >
            結束數據迷航。<br />
            讓決策，<br />
            <span className="font-serif italic font-normal text-chrome-gradient">一目了然</span>。
          </motion.h1>
          
          {/* 段落 - 極高可讀性與高雅的排版間距 */}
          <motion.p 
            variants={itemVariants}
            className="text-base md:text-lg text-slate-400 mb-10 max-w-xl leading-relaxed font-light tracking-wide"
          >
            DataVue 將 Facebook Ads、GSC 與 GA4 的紛亂雜音，煉化為清晰的單一事實。
            藉由反向工程行銷數據，AI 隨時為您指引具備「勝負感」的致勝策略。
          </motion.p>
          
          {/* 按鈕組 */}
          <motion.div 
            variants={itemVariants}
            className="flex flex-col sm:flex-row items-center gap-5 w-full sm:w-auto"
          >
            <motion.button 
              whileHover={{ scale: 1.02, y: -2 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => navigate('/login')}
              className="w-full sm:w-auto px-8 py-4 rounded-full bg-white text-black font-display font-semibold text-sm tracking-wider uppercase transition-all duration-300 shadow-[0_10px_30px_rgba(255,255,255,0.08)] flex items-center justify-center gap-2 hover:shadow-[0_15px_40px_rgba(255,255,255,0.18)]"
            >
              即刻免費啟用 <ArrowRight className="w-4 h-4 stroke-[2.5px]" />
            </motion.button>
            
            <motion.a 
              href="#features"
              whileHover={{ x: 3 }}
              className="w-full sm:w-auto px-8 py-4 rounded-full border border-white/5 bg-white/[0.02] hover:bg-white/[0.06] text-slate-300 hover:text-white font-display text-sm tracking-wide transition-all duration-300 flex items-center justify-center gap-2"
            >
              探尋引擎機密
            </motion.a>
          </motion.div>
        </motion.div>

        {/* 右側：動態「數據熔爐 (The Data Fusion Nexus)」3D/CSS 動態雕塑 */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.95, y: 30 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.5, ease: [0.16, 1, 0.3, 1] }}
          className="lg:col-span-5 w-full aspect-square relative flex items-center justify-center"
        >
          {/* 數據熔爐主體 (The Reactor Hub) */}
          <div className="w-full max-w-[400px] aspect-square rounded-full border border-white/[0.03] bg-gradient-to-b from-white/[0.02] to-transparent flex items-center justify-center relative p-8 group">
            {/* 旋轉外環 */}
            <div className="absolute inset-0 rounded-full border border-dashed border-white/10 animate-[spin_60s_linear_infinite]" />
            {/* 逆向旋轉中環 */}
            <div className="absolute inset-8 rounded-full border border-white/5 animate-[spin_30s_linear_infinite_reverse] flex items-center justify-center">
              <div className="w-full h-[1px] bg-gradient-to-r from-transparent via-white/20 to-transparent" />
            </div>
            {/* 發光的偏心內環 */}
            <div className="absolute inset-16 rounded-full border border-white/10 bg-[#090b0f]/80 backdrop-blur-md flex items-center justify-center shadow-[inset_0_1px_20px_rgba(255,255,255,0.02)]">
              {/* 核心 AI 狀態圖示 */}
              <div className="relative w-20 h-20 flex items-center justify-center">
                <div className="absolute inset-0 bg-brand-purple/10 rounded-full blur-md animate-pulse" />
                <Activity className="w-8 h-8 text-brand-cyan animate-pulse relative z-10" />
              </div>
            </div>

            {/* 平台流光引線 (模擬 Facebook, GSC, GA4 流向核心的動態粒子軌跡) */}
            
            {/* 1. Facebook Ads 軌跡 */}
            <div className="absolute -top-6 left-12 p-3 glass border-white/5 bg-[#090b0f]/60 backdrop-blur-md flex items-center gap-3 hover:border-brand-blue/30 transition-colors group/item">
              <div className="w-6 h-6 rounded-full bg-brand-blue/20 flex items-center justify-center text-brand-blue text-xs font-semibold">F</div>
              <div className="text-[10px] font-display">
                <div className="text-slate-400 uppercase tracking-widest">FB Ads CTR</div>
                <div className="text-white font-bold">4.28%</div>
              </div>
            </div>
            {/* 2. GSC 軌跡 */}
            <div className="absolute top-1/2 -right-8 -translate-y-1/2 p-3 glass border-white/5 bg-[#090b0f]/60 backdrop-blur-md flex items-center gap-3 hover:border-brand-cyan/30 transition-colors group/item">
              <div className="w-6 h-6 rounded-full bg-brand-cyan/20 flex items-center justify-center text-brand-cyan text-xs font-semibold">G</div>
              <div className="text-[10px] font-display">
                <div className="text-slate-400 uppercase tracking-widest">GSC Impressions</div>
                <div className="text-white font-bold">142.8K</div>
              </div>
            </div>
            {/* 3. GA4 軌跡 */}
            <div className="absolute -bottom-6 left-1/4 p-3 glass border-white/5 bg-[#090b0f]/60 backdrop-blur-md flex items-center gap-3 hover:border-brand-purple/30 transition-colors group/item">
              <div className="w-6 h-6 rounded-full bg-brand-purple/20 flex items-center justify-center text-brand-purple text-xs font-semibold">A</div>
              <div className="text-[10px] font-display">
                <div className="text-slate-400 uppercase tracking-widest">GA4 Bounce Rate</div>
                <div className="text-white font-bold">34.2%</div>
              </div>
            </div>

            {/* 動態連線 (SVG Overlay) */}
            <svg className="absolute inset-0 w-full h-full pointer-events-none -z-10" viewBox="0 0 400 400">
              <defs>
                <linearGradient id="blue-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.8" />
                  <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0" />
                </linearGradient>
                <linearGradient id="cyan-grad" x1="100%" y1="50%" x2="50%" y2="50%">
                  <stop offset="0%" stopColor="#06b6d4" stopOpacity="0.8" />
                  <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0" />
                </linearGradient>
                <linearGradient id="purple-grad" x1="25%" y1="100%" x2="50%" y2="50%">
                  <stop offset="0%" stopColor="#8b5cf6" stopOpacity="0.8" />
                  <stop offset="100%" stopColor="#3b82f6" stopOpacity="0" />
                </linearGradient>
              </defs>
              {/* 繪製流光通道 */}
              <path d="M 120 0 Q 150 150 200 200" fill="none" stroke="url(#blue-grad)" strokeWidth="1" strokeDasharray="5,5" className="animate-[dash_10s_linear_infinite]" />
              <path d="M 400 200 Q 250 200 200 200" fill="none" stroke="url(#cyan-grad)" strokeWidth="1" strokeDasharray="5,5" className="animate-[dash_10s_linear_infinite]" />
              <path d="M 100 400 Q 150 250 200 200" fill="none" stroke="url(#purple-grad)" strokeWidth="1" strokeDasharray="5,5" className="animate-[dash_10s_linear_infinite]" />
            </svg>
          </div>

          {/* AI 實時解譯卡片浮動在下方 */}
          <div className="absolute bottom-4 right-0 md:-right-8 p-4 glass border-white/5 bg-black/80 backdrop-blur-2xl max-w-[280px] shadow-[0_20px_50px_rgba(0,0,0,0.7)]">
            <div className="flex items-center gap-2 mb-2">
              <Sparkles className="w-3.5 h-3.5 text-brand-purple" />
              <span className="text-[10px] font-display font-bold tracking-widest text-brand-purple uppercase">AI Synthesis Engine</span>
            </div>
            <p className="text-[11px] text-slate-300 leading-relaxed">
              「偵測到 Facebook 廣告存在受眾重疊，而 GSC 指向高意圖關鍵字。建議將 15% 預算轉移至精準著陸頁。」
            </p>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
