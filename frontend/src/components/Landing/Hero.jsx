import { motion } from 'motion';
import { ArrowRight, Play } from 'lucide-react';

export default function Hero() {
  return (
    <section className="relative pt-32 pb-20 px-6 overflow-hidden bg-mesh min-h-screen flex flex-col items-center justify-center">
      {/* Background Glows */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-brand-blue/20 rounded-full blur-[120px] -z-10" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-brand-purple/20 rounded-full blur-[120px] -z-10" />

      <motion.div 
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.2 }}
        className="max-w-4xl mx-auto text-center"
      >
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full glass border-white/10 mb-8">
          <span className="w-2 h-2 rounded-full bg-brand-cyan animate-pulse" />
          <span className="text-xs font-semibold tracking-widest text-brand-cyan uppercase">System Internal: Site-tegy Ready</span>
        </div>
        
        <h1 className="text-5xl md:text-7xl font-display font-bold mb-6 leading-tight">
          DataVue ??<span className="text-gradient">?∏Ê??®ÊôØ</span><br />
          ‰∏Ä?Æ‰???        </h1>
        
        <p className="text-lg md:text-xl text-slate-400 mb-10 max-w-2xl mx-auto leading-relaxed">
          ÁµÇÁ??∏Ê?Ëø∑Ëà™?Ç‰?Á´ôÂ??¥Â? Facebook Ads?ÅGoogle Search Console ??GA4ÔºåË? AI Â∞áÊÇ®?ÑÂÜ∞?∑Êï∏Â≠óË??ñÁÇ∫?¥Â??∞Áï•??        </p>
        
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <motion.button 
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="w-full sm:w-auto bg-white text-black px-8 py-4 rounded-2xl font-bold text-lg flex items-center justify-center gap-2 shadow-[0_0_20px_rgba(255,255,255,0.3)]"
          >
            ?çË≤ªÈ´îÈ? <ArrowRight className="w-5 h-5" />
          </motion.button>
          
          <motion.button 
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="w-full sm:w-auto glass hover:bg-white/10 px-8 py-4 rounded-2xl font-bold text-lg flex items-center justify-center gap-2 text-white border-white/20 transition-colors"
          >
            <Play className="w-5 h-5 fill-current" /> ‰∫ÜËß£?ã‰??πÂ?
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
        <div className="absolute inset-0 bg-gradient-to-t from-background via-transparent to-transparent z-10" />
        <div className="glass rounded-3xl overflow-hidden border border-white/10 shadow-2xl">
          <div className="h-8 bg-white/5 border-b border-white/10 flex items-center px-4 gap-2">
            <div className="w-2.5 h-2.5 rounded-full bg-red-500/50" />
            <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/50" />
            <div className="w-2.5 h-2.5 rounded-full bg-green-500/50" />
          </div>
          <div className="p-8 bg-slate-900/50 aspect-video flex items-center justify-center relative">
             <div className="grid grid-cols-3 gap-6 w-full">
                <div className="h-32 rounded-xl bg-white/5 animate-pulse" />
                <div className="h-32 rounded-xl bg-white/5 animate-pulse delay-75" />
                <div className="h-32 rounded-xl bg-white/5 animate-pulse delay-150" />
                <div className="h-64 col-span-2 rounded-xl bg-white/5 animate-pulse delay-300" />
                <div className="h-64 rounded-xl bg-white/5 animate-pulse delay-500" />
             </div>
             <div className="absolute inset-0 flex items-center justify-center">
                <div className="glass p-6 rounded-2xl border-white/20 shadow-2xl backdrop-blur-2xl">
                   <div className="text-brand-cyan font-mono text-sm mb-2">Analyzing Intent...</div>
                   <div className="text-white font-medium">?ºÁèæ 12 ?ãÈ??àÈ??µÂ?Ê©üÊ?</div>
                </div>
             </div>
          </div>
        </div>
      </motion.div>
    </section>
  );
}

