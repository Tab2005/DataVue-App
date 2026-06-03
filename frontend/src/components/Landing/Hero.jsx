import { motion } from 'framer-motion';
import { ArrowRight, Play } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function Hero() {
  const navigate = useNavigate();

  return (
    <section className="relative pt-32 pb-20 px-6 overflow-hidden bg-mesh min-h-screen flex flex-col items-center justify-center">
      {/* Background Glows */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-brand-blue/10 rounded-full blur-[120px] -z-10" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-brand-orange/10 rounded-full blur-[120px] -z-10" />

      <motion.div 
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.2 }}
        className="max-w-4xl mx-auto text-center"
      >
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full glass border-white/5 mb-8">
          <span className="w-2 h-2 rounded-full bg-brand-orange animate-pulse" />
          <span className="text-xs font-display font-medium tracking-widest text-brand-orange uppercase">Engine Status: DataVue Core Ready</span>
        </div>
        
        <h1 className="text-5xl md:text-7xl font-sans font-bold mb-6 leading-tight text-white tracking-tight">
          DataVue — <span className="text-gradient">數據全景</span><br />
          決策一目了然
        </h1>
        
        <p className="text-lg md:text-xl text-slate-400 mb-10 max-w-2xl mx-auto leading-relaxed">
          透過反向工程行銷數據，終結多平台迷航。一站式整合 Facebook Ads、Google Search Console 與 GA4，讓 AI 將您的冰冷數字轉化為致勝戰略。
        </p>
        
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <motion.button 
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            onClick={() => navigate('/login')}
            className="w-full sm:w-auto bg-brand-orange hover:bg-brand-orange-hover text-white px-8 py-4 rounded-2xl font-bold text-lg flex items-center justify-center gap-2 shadow-[0_0_20px_rgba(249,115,22,0.3)] transition-colors"
          >
            免費體驗 <ArrowRight className="w-5 h-5" />
          </motion.button>
          
          <motion.button 
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            className="w-full sm:w-auto glass hover:bg-white/5 px-8 py-4 rounded-2xl font-bold text-lg flex items-center justify-center gap-2 text-slate-300 border-white/10 transition-colors"
          >
            <Play className="w-5 h-5 fill-current" /> 了解運作方式
          </motion.button>
        </div>
      </motion.div>

      {/* Hero Visual - Dashboard Preview Mockup */}
      <motion.div 
        initial={{ opacity: 0, y: 100 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1, delay: 0.6 }}
        className="mt-20 w-full max-w-5xl mx-auto relative group"
      >
        <div className="absolute inset-0 bg-gradient-to-t from-[#0f172a] via-transparent to-transparent z-10" />
        <div className="glass rounded-3xl overflow-hidden border border-white/5 shadow-2xl bg-slate-900/30">
          <div className="h-10 bg-slate-900/80 border-b border-white/5 flex items-center px-4 justify-between">
            <div className="flex gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500/40" />
              <div className="w-3 h-3 rounded-full bg-yellow-500/40" />
              <div className="w-3 h-3 rounded-full bg-green-500/40" />
            </div>
            <div className="text-xs font-display text-slate-500">datavue_dashboard_preview.py</div>
            <div className="w-12" />
          </div>
          <div className="p-8 bg-slate-950/40 aspect-video flex items-center justify-center relative">
             <div className="grid grid-cols-3 gap-6 w-full">
                <div className="h-32 rounded-xl bg-white/5 border border-white/5 animate-pulse flex flex-col justify-between p-4">
                  <div className="text-xs font-display text-slate-500">FACEBOOK ADS CTR</div>
                  <div className="text-2xl font-display font-semibold text-brand-orange">4.28%</div>
                  <div className="text-[10px] text-emerald-400 font-display">+1.12% YoY</div>
                </div>
                <div className="h-32 rounded-xl bg-white/5 border border-white/5 animate-pulse delay-75 flex flex-col justify-between p-4">
                  <div className="text-xs font-display text-slate-500">GSC IMPRESSIONS</div>
                  <div className="text-2xl font-display font-semibold text-brand-blue">142.8K</div>
                  <div className="text-[10px] text-emerald-400 font-display">+18.4% MoM</div>
                </div>
                <div className="h-32 rounded-xl bg-white/5 border border-white/5 animate-pulse delay-150 flex flex-col justify-between p-4">
                  <div className="text-xs font-display text-slate-500">GA4 CONVERSIONS</div>
                  <div className="text-2xl font-display font-semibold text-white">8.42%</div>
                  <div className="text-[10px] text-brand-orange font-display">Target Reached</div>
                </div>
                <div className="h-64 col-span-2 rounded-xl bg-white/5 border border-white/5 animate-pulse delay-300 p-6 flex flex-col justify-between">
                  <div className="text-xs font-display text-slate-400">INTEGRATED TRAFFIC & REVENUE MATCH</div>
                  <div className="flex-1 flex items-end gap-3 mt-4">
                    <div className="w-full bg-brand-blue/30 h-1/3 rounded-t-md" />
                    <div className="w-full bg-brand-orange/30 h-1/2 rounded-t-md" />
                    <div className="w-full bg-brand-blue/40 h-2/3 rounded-t-md" />
                    <div className="w-full bg-brand-orange/50 h-3/4 rounded-t-md" />
                    <div className="w-full bg-brand-blue/50 h-5/6 rounded-t-md" />
                    <div className="w-full bg-brand-orange/80 h-full rounded-t-md" />
                  </div>
                </div>
                <div className="h-64 rounded-xl bg-white/5 border border-white/5 animate-pulse delay-500 p-6 flex flex-col justify-between">
                  <div className="text-xs font-display text-slate-400">AI INSIGHT LOG</div>
                  <div className="flex-1 flex flex-col gap-2 mt-4 font-display text-[11px] text-slate-400">
                    <div className="text-emerald-400">&gt; FB Ads budget reallocation: Success</div>
                    <div className="text-brand-blue">&gt; GSC search intent shift detected</div>
                    <div className="text-brand-orange">&gt; AI Agent suggesting CTR optimization</div>
                    <div className="text-slate-600">&gt; Waiting for manual approval...</div>
                  </div>
                </div>
             </div>
             <div className="absolute inset-0 flex items-center justify-center">
                <div className="glass p-6 rounded-2xl border-white/10 shadow-2xl backdrop-blur-2xl bg-slate-900/60 max-w-sm">
                   <div className="text-brand-orange font-display text-xs mb-2 tracking-widest uppercase">&gt; AI Intent Analyzer</div>
                   <div className="text-white font-sans text-sm font-medium">檢測到 8 個 Facebook 廣告組存在受眾重疊，AI 已為您完成預算整合。</div>
                </div>
             </div>
          </div>
        </div>
      </motion.div>
    </section>
  );
}
