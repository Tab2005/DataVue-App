import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { FaFacebook, FaGoogle } from 'react-icons/fa';
import { SiGooglecloud } from 'react-icons/si';

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.12, delayChildren: 0.3 }
  }
};

const itemVariants = {
  hidden: { y: 40, opacity: 0 },
  visible: { y: 0, opacity: 1, transition: { duration: 0.8, ease: [0.16, 1, 0.3, 1] } }
};

export default function Hero() {
  const navigate = useNavigate();

  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden pt-20 pb-16">
      {/* 動態粒子背景 */}
      <div className="absolute inset-0 overflow-hidden">
        {/* 主要漸層光暈 */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px]">
          <div className="absolute inset-0 bg-gradient-radial from-cyan-500/10 via-purple-500/5 to-transparent rounded-full animate-pulse-slow" />
        </div>

        {/* 左側藍光 */}
        <div className="absolute top-1/3 left-0 w-96 h-96 bg-blue-500/10 rounded-full blur-[150px] animate-float-left" />

        {/* 右側紫光 */}
        <div className="absolute bottom-1/4 right-0 w-96 h-96 bg-purple-500/10 rounded-full blur-[150px] animate-float-right" />

        {/* 底部青色光 */}
        <div className="absolute bottom-0 left-1/3 w-80 h-80 bg-cyan-500/8 rounded-full blur-[120px] animate-float-center" />

        {/* 旋轉粒子環 */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px]">
          <div className="absolute inset-0 border border-dashed border-cyan-500/10 rounded-full animate-spin-slow" />
          <div className="absolute inset-8 border border-dashed border-purple-500/10 rounded-full animate-spin-reverse" />
          <div className="absolute inset-16 border border-blue-500/10 rounded-full animate-spin-slow" />
        </div>

        {/* 漂浮數據節點 */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1, transition: { delay: 1.5, duration: 1 } }}
          className="absolute top-20 left-[15%] w-3 h-3 bg-cyan-400/50 rounded-full animate-float-node-1"
        />
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1, transition: { delay: 1.8, duration: 1 } }}
          className="absolute top-40 right-[20%] w-2 h-2 bg-purple-400/50 rounded-full animate-float-node-2"
        />
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1, transition: { delay: 2.1, duration: 1 } }}
          className="absolute bottom-32 left-[25%] w-2.5 h-2.5 bg-blue-400/50 rounded-full animate-float-node-3"
        />
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1, transition: { delay: 2.4, duration: 1 } }}
          className="absolute bottom-48 right-[15%] w-2 h-2 bg-cyan-300/50 rounded-full animate-float-node-4"
        />
      </div>

      <div className="max-w-7xl mx-auto px-6 w-full relative z-10">
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-center"
        >
          {/* 左側：文案區 */}
          <div className="lg:col-span-6 flex flex-col items-start">
            {/* 狀態標籤 */}
            <motion.div variants={itemVariants} className="status-tag mb-8">
              <span className="status-dot" />
              <span>AI 核心引擎已就緒</span>
            </motion.div>

            {/* 主標題 */}
            <motion.h1 variants={itemVariants} className="hero-title mb-6">
              匯聚所有數據
              <br />
              <span className="gradient-text">洞察一觸即達</span>
            </motion.h1>

            {/* 副標題 */}
            <motion.p variants={itemVariants} className="hero-subtitle mb-10">
              Facebook Ads、Google Search Console、GA4 — 所有行銷數據在同一個宇宙中匯聚。
              DataVue 以 AI 為核心，為您提煉出可付諸行動的商業洞察。
            </motion.p>

            {/* CTA 按鈕組 */}
            <motion.div variants={itemVariants} className="flex flex-col sm:flex-row gap-4 w-full sm:w-auto">
              <motion.button
                whileHover={{ scale: 1.02, boxShadow: '0 0 40px rgba(6, 182, 212, 0.4)' }}
                whileTap={{ scale: 0.98 }}
                onClick={() => navigate('/login')}
                className="cta-button-primary"
              >
                探索數據宇宙
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </motion.button>

              <motion.a
                href="#features"
                whileHover={{ x: 4 }}
                className="cta-button-secondary"
              >
                了解核心功能
              </motion.a>
            </motion.div>

            {/* 數據來源標識 */}
            <motion.div variants={itemVariants} className="mt-12 flex items-center gap-6">
              <span className="text-xs text-slate-500 font-medium tracking-wider">整合來源</span>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 border border-white/5 hover:border-blue-500/30 transition-colors">
                  <FaFacebook className="w-4 h-4 text-blue-400" />
                  <span className="text-xs text-slate-400">Facebook</span>
                </div>
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 border border-white/5 hover:border-green-500/30 transition-colors">
                  <SiGooglecloud className="w-4 h-4 text-green-400" />
                  <span className="text-xs text-slate-400">GSC</span>
                </div>
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 border border-white/5 hover:border-yellow-500/30 transition-colors">
                  <FaGoogle className="w-4 h-4 text-yellow-400" />
                  <span className="text-xs text-slate-400">GA4</span>
                </div>
              </div>
            </motion.div>
          </div>

          {/* 右側：動態數據星核視覺化 */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 1, delay: 0.5, ease: [0.16, 1, 0.3, 1] }}
            className="lg:col-span-6 flex items-center justify-center relative"
          >
            {/* 外層光環 */}
            <div className="absolute inset-0 bg-gradient-to-tr from-cyan-500/20 via-purple-500/20 to-blue-500/20 rounded-full blur-3xl animate-pulse" />

            {/* 主體容器 */}
            <div className="relative w-full max-w-lg aspect-square">
              {/* 旋轉外環 */}
              <div className="absolute inset-0 rounded-full border border-dashed border-cyan-500/20 animate-orbit-1" />
              <div className="absolute inset-4 rounded-full border border-dashed border-purple-500/15 animate-orbit-2" />
              <div className="absolute inset-8 rounded-full border border-blue-500/10 animate-orbit-1" />

              {/* 核心球體 */}
              <div className="absolute inset-16 rounded-full bg-gradient-to-br from-slate-900 via-slate-800 to-black border border-white/10 shadow-2xl flex items-center justify-center overflow-hidden">
                {/* 核心光暈 */}
                <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/10 via-transparent to-purple-500/10" />

                {/* 核心脈動 */}
                <div className="absolute inset-8 rounded-full bg-gradient-to-br from-cyan-500/20 to-purple-500/20 animate-pulse-subtle" />

                {/* 核心數據流 */}
                <div className="relative z-10 w-20 h-20 rounded-full bg-gradient-to-br from-cyan-400 via-purple-500 to-blue-500 flex items-center justify-center">
                  <div className="absolute inset-1 rounded-full bg-slate-900 flex items-center justify-center">
                    <Database className="w-8 h-8 text-white" />
                  </div>
                </div>

                {/* 內部光環 */}
                <div className="absolute inset-0 rounded-full border border-white/5 animate-spin-slow" />
              </div>

              {/* 浮動數據卡 - Facebook */}
              <motion.div
                animate={{ y: [0, -8, 0] }}
                transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
                className="absolute top-8 left-8 glass-card"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center">
                    <FaFacebook className="w-4 h-4 text-blue-400" />
                  </div>
                  <div>
                    <div className="text-[10px] text-slate-500 uppercase tracking-wider">ROAS</div>
                    <div className="text-sm font-bold text-white">3.2x</div>
                  </div>
                </div>
              </motion.div>

              {/* 浮動數據卡 - GSC */}
              <motion.div
                animate={{ y: [0, 8, 0] }}
                transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut', delay: 0.5 }}
                className="absolute top-20 right-4 glass-card"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-green-500/20 flex items-center justify-center">
                    <SiGooglecloud className="w-4 h-4 text-green-400" />
                  </div>
                  <div>
                    <div className="text-[10px] text-slate-500 uppercase tracking-wider">曝光</div>
                    <div className="text-sm font-bold text-white">+142%</div>
                  </div>
                </div>
              </motion.div>

              {/* 浮動數據卡 - GA4 */}
              <motion.div
                animate={{ y: [0, -6, 0] }}
                transition={{ duration: 3.5, repeat: Infinity, ease: 'easeInOut', delay: 1 }}
                className="absolute bottom-16 left-12 glass-card"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-yellow-500/20 flex items-center justify-center">
                    <FaGoogle className="w-4 h-4 text-yellow-400" />
                  </div>
                  <div>
                    <div className="text-[10px] text-slate-500 uppercase tracking-wider">轉換率</div>
                    <div className="text-sm font-bold text-white">4.28%</div>
                  </div>
                </div>
              </motion.div>

              {/* AI 洞察卡片 */}
              <motion.div
                animate={{ y: [0, 10, 0] }}
                transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut', delay: 1.5 }}
                className="absolute bottom-8 right-8 glass-card border-cyan-500/20"
              >
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
                  <span className="text-[10px] text-cyan-400 font-semibold tracking-wider">AI 分析</span>
                </div>
                <p className="text-xs text-slate-400 leading-relaxed max-w-[180px]">
                  檢測到高意圖關鍵字，建議將 20% 預算重新分配
                </p>
              </motion.div>

              {/* 連接線 SVG */}
              <svg className="absolute inset-0 w-full h-full pointer-events-none">
                <defs>
                  <linearGradient id="line-gradient-1" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#06b6d4" stopOpacity="0.5" />
                    <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0" />
                  </linearGradient>
                  <linearGradient id="line-gradient-2" x1="100%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor="#8b5cf6" stopOpacity="0.5" />
                    <stop offset="100%" stopColor="#06b6d4" stopOpacity="0" />
                  </linearGradient>
                </defs>
                <motion.path
                  d="M 80 80 Q 150 150 200 200"
                  fill="none"
                  stroke="url(#line-gradient-1)"
                  strokeWidth="1"
                  strokeDasharray="4,4"
                  initial={{ pathLength: 0 }}
                  animate={{ pathLength: 1 }}
                  transition={{ duration: 2, delay: 1 }}
                />
                <motion.path
                  d="M 320 100 Q 250 150 200 200"
                  fill="none"
                  stroke="url(#line-gradient-2)"
                  strokeWidth="1"
                  strokeDasharray="4,4"
                  initial={{ pathLength: 0 }}
                  animate={{ pathLength: 1 }}
                  transition={{ duration: 2, delay: 1.2 }}
                />
              </svg>
            </div>
          </motion.div>
        </motion.div>

        {/* 滾動提示 */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 2, duration: 1 }}
          className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2"
        >
          <span className="text-[10px] text-slate-500 tracking-widest uppercase">向下探索</span>
          <motion.div
            animate={{ y: [0, 8, 0] }}
            transition={{ duration: 1.5, repeat: Infinity }}
            className="w-5 h-8 rounded-full border border-slate-600 flex justify-center pt-2"
          >
            <div className="w-1 h-1.5 rounded-full bg-slate-500" />
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}

function Database({ className }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 0v3.75m-16.5-3.75v3.75m16.5 0v3.75C20.25 16.153 16.556 18 12 18s-8.25-1.847-8.25-4.125v-3.75m16.5 0c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125" />
    </svg>
  );
}