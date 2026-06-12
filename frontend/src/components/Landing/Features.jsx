import { motion, AnimatePresence } from 'framer-motion';
import { useState } from 'react';
import { FaFacebook } from 'react-icons/fa';
import { SiGooglecloud } from 'react-icons/si';
import { Search, BarChart3, Bot, Sparkles, TrendingUp, Target, Zap, Shield } from 'lucide-react';

const features = [
  {
    id: 'gsc',
    icon: SiGooglecloud,
    color: 'green',
    title: 'GSC 搜尋意圖解碼',
    subtitle: 'Search Console Intelligence',
    description: '不只是追蹤排名。深入剖析關鍵字背後的真實搜尋意圖 — 知識型、比較型、交易型。為您揭示用戶的真正需求，引導精準內容策略。',
    stats: { label: '搜尋點擊率提升', value: '+18.4%' },
    visual: 'chart'
  },
  {
    id: 'fb',
    icon: FaFacebook,
    color: 'blue',
    title: 'Facebook Ads 實時追蹤',
    subtitle: 'Ads Intelligence',
    description: '打破 Facebook 歸因的黑盒子。實時監控廣告受眾重疊率與真實轉化漏斗，防止預算在重疊受眾中相互競價而浪費。',
    stats: { label: '平均轉化成本降低', value: '-24.1%' },
    visual: 'funnel'
  },
  {
    id: 'ga4',
    icon: BarChart3,
    color: 'purple',
    title: 'GA4 流量與行為還原',
    subtitle: 'Analytics Intelligence',
    description: '將 GA4 複雜的事件還原成直觀的用戶旅程地圖。自動進行多維度內容分組，精準找出導致高跳出率的頁面問題。',
    stats: { label: '核心頁面停留提升', value: '+42.6%' },
    visual: 'funnel'
  },
  {
    id: 'ai',
    icon: Bot,
    color: 'cyan',
    title: 'AI 戰略智庫',
    subtitle: 'Intelligence Core',
    description: '24小時不休的虛擬數據分析師。整合多平台數據，自動進行數據清洗與關聯性建模，產出可執行的決策報告。',
    stats: { label: '決策響應速度', value: '10x' },
    visual: 'neural'
  }
];

const colorClasses = {
  green: {
    bg: 'bg-green-500/10',
    border: 'border-green-500/30',
    text: 'text-green-400',
    glow: 'shadow-green-500/20',
    gradient: 'from-green-500/20 to-transparent'
  },
  blue: {
    bg: 'bg-blue-500/10',
    border: 'border-blue-500/30',
    text: 'text-blue-400',
    glow: 'shadow-blue-500/20',
    gradient: 'from-blue-500/20 to-transparent'
  },
  purple: {
    bg: 'bg-purple-500/10',
    border: 'border-purple-500/30',
    text: 'text-purple-400',
    glow: 'shadow-purple-500/20',
    gradient: 'from-purple-500/20 to-transparent'
  },
  cyan: {
    bg: 'bg-cyan-500/10',
    border: 'border-cyan-500/30',
    text: 'text-cyan-400',
    glow: 'shadow-cyan-500/20',
    gradient: 'from-cyan-500/20 to-transparent'
  }
};

export default function Features() {
  const [activeTab, setActiveTab] = useState('gsc');
  const currentFeature = features.find(f => f.id === activeTab);
  const colors = colorClasses[currentFeature.color];

  return (
    <section id="features" className="relative py-32 px-6 overflow-hidden">
      {/* 背景裝飾 */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-slate-900/50 to-transparent" />
      <div className={`absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[400px] bg-gradient-to-b ${colors.gradient} rounded-full blur-[150px] opacity-50`} />

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
            <Zap className="w-3.5 h-3.5 text-cyan-400" />
            <span>核心數據引擎</span>
          </div>
          <h2 className="section-title mb-4">
            四大數據支柱
            <br />
            <span className="gradient-text">構築商業洞察</span>
          </h2>
          <p className="section-subtitle max-w-2xl mx-auto">
            每個平台都是洞察的碎片。DataVue 將它們熔煉成完整的商業地圖。
          </p>
        </motion.div>

        {/* 主內容區 */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* 左側：功能導航 */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
            className="lg:col-span-5 flex flex-col gap-4"
          >
            {features.map((feature, index) => {
              const featureColors = colorClasses[feature.color];
              const isActive = activeTab === feature.id;

              return (
                <motion.button
                  key={feature.id}
                  onClick={() => setActiveTab(feature.id)}
                  whileHover={{ x: 4 }}
                  className={`
                    relative w-full text-left p-5 rounded-2xl border transition-all duration-500
                    ${isActive
                      ? `${featureColors.bg} ${featureColors.border} shadow-lg ${featureColors.glow}`
                      : 'bg-slate-900/30 border-white/5 hover:border-white/10'
                    }
                  `}
                >
                  {/* 激活指示器 */}
                  {isActive && (
                    <motion.div
                      layoutId="active-indicator"
                      className={`absolute left-0 top-4 bottom-4 w-[3px] bg-gradient-to-b ${featureColors.gradient} rounded-full`}
                    />
                  )}

                  <div className="flex items-center gap-4 relative z-10">
                    <div className={`w-12 h-12 rounded-xl flex items-center justify-center border transition-all duration-300 ${
                      isActive
                        ? `bg-white/10 border-white/20 ${featureColors.text}`
                        : 'bg-white/5 border-white/5 text-slate-500'
                    }`}>
                      <feature.icon className="w-5 h-5" />
                    </div>
                    <div className="flex-1">
                      <h3 className={`font-semibold mb-1 transition-colors ${
                        isActive ? 'text-white' : 'text-slate-400'
                      }`}>
                        {feature.title}
                      </h3>
                      <span className="text-[10px] text-slate-500 uppercase tracking-wider">
                        {feature.subtitle}
                      </span>
                    </div>
                    <TrendingUp className={`w-4 h-4 transition-all duration-300 ${
                      isActive ? `${featureColors.text} opacity-100 translate-x-0` : 'text-slate-600 opacity-0 -translate-x-2'
                    }`} />
                  </div>
                </motion.button>
              );
            })}
          </motion.div>

          {/* 右側：功能詳情面板 */}
          <motion.div
            initial={{ opacity: 0, x: 30 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="lg:col-span-7"
          >
            <div className={`relative rounded-3xl border ${colors.border} bg-slate-900/50 backdrop-blur-xl p-8 lg:p-10 overflow-hidden shadow-2xl ${colors.glow}`}>
              {/* 背景光暈 */}
              <div className={`absolute top-0 right-0 w-64 h-64 bg-gradient-to-br ${colors.gradient} rounded-full blur-[100px] opacity-60`} />

              <AnimatePresence mode="wait">
                <motion.div
                  key={activeTab}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
                  className="relative z-10"
                >
                  {/* 面板頂部 */}
                  <div className="flex items-center justify-between mb-8 pb-6 border-b border-white/5">
                    <div className="flex items-center gap-2">
                      <div className={`w-2.5 h-2.5 rounded-full ${colors.bg} ${colors.text}`} />
                      <div className={`w-2.5 h-2.5 rounded-full ${colors.bg} ${colors.text} opacity-50`} />
                      <div className={`w-2.5 h-2.5 rounded-full ${colors.bg} ${colors.text} opacity-25`} />
                    </div>
                    <div className={`flex items-center gap-2 px-3 py-1 rounded-full border ${colors.border} ${colors.bg}`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${colors.text} animate-pulse`} />
                      <span className={`text-[10px] font-medium ${colors.text} uppercase tracking-wider`}>Live</span>
                    </div>
                  </div>

                  {/* 主要內容 */}
                  <div className="mb-8">
                    <h3 className={`text-2xl lg:text-3xl font-bold mb-3 ${colors.text}`}>
                      {currentFeature.title}
                    </h3>
                    <p className="text-slate-400 text-sm lg:text-base leading-relaxed">
                      {currentFeature.description}
                    </p>
                  </div>

                  {/* 視覺化區域 */}
                  <div className={`h-40 rounded-2xl border ${colors.border} bg-black/40 p-5 mb-8 overflow-hidden`}>
                    {activeTab === 'gsc' && <GSCVisual colors={colors} />}
                    {activeTab === 'fb' && <FBVisual colors={colors} />}
                    {activeTab === 'ga4' && <GA4Visual colors={colors} />}
                    {activeTab === 'ai' && <AIVisual colors={colors} />}
                  </div>

                  {/* 底部統計 */}
                  <div className="flex items-center justify-between pt-6 border-t border-white/5">
                    <div>
                      <div className={`text-[10px] ${colors.text} uppercase tracking-widest mb-1`}>
                        {currentFeature.stats.label}
                      </div>
                      <div className={`text-3xl font-bold ${colors.text}`}>
                        {currentFeature.stats.value}
                      </div>
                    </div>
                    <div className={`flex items-center gap-2 px-4 py-2 rounded-full border ${colors.border} ${colors.bg}`}>
                      <Target className={`w-4 h-4 ${colors.text}`} />
                      <span className="text-xs text-slate-400">關鍵指標</span>
                    </div>
                  </div>
                </motion.div>
              </AnimatePresence>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}

// 視覺化組件
function GSCVisual({ colors }) {
  return (
    <div className="h-full flex flex-col justify-between font-mono text-[10px]">
      <div className="flex justify-between items-center text-slate-500 border-b border-white/5 pb-2">
        <span>INTENT TYPE</span>
        <span>KEYWORDS</span>
        <span>GROWTH</span>
      </div>
      <div className="flex-1 flex items-center justify-between mt-3">
        <div className="flex flex-col gap-2">
          <span className={`px-2 py-1 rounded bg-${colors.color}-500/10 border border-${colors.color}-500/20 ${colors.text} font-semibold`}>TRANSACTIONAL</span>
          <span className="px-2 py-1 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-semibold">COMMERCIAL</span>
        </div>
        <div className="text-slate-400 space-y-1">
          <div>「跨境電商系統」</div>
          <div className="opacity-50">「行銷工具推薦」</div>
        </div>
        <div className={`text-right font-bold ${colors.text}`}>
          <div>+342%</div>
          <div className="text-emerald-400 opacity-70">+128%</div>
        </div>
      </div>
    </div>
  );
}

function FBVisual({ colors }) {
  return (
    <div className="h-full flex flex-col justify-between">
      <div className="flex justify-between items-center text-[10px] text-slate-500 border-b border-white/5 pb-2">
        <span>AD SET</span>
        <span>ROAS</span>
        <span>BUDGET</span>
      </div>
      <div className="flex-1 flex items-end gap-4 mt-4 justify-center">
        <div className="flex flex-col items-center gap-2">
          <div className="w-16 bg-blue-500/20 border border-blue-500/30 rounded-t-lg flex flex-col justify-end p-2" style={{ height: '60%' }}>
            <span className="text-[8px] text-slate-400">A</span>
            <span className="text-sm font-bold text-white">1.8x</span>
          </div>
          <span className="text-[8px] text-slate-500">Ad Set A</span>
        </div>
        <div className="flex flex-col items-center gap-2">
          <div className="w-16 bg-cyan-500/20 border border-cyan-500/30 rounded-t-lg flex flex-col justify-end p-2" style={{ height: '90%' }}>
            <span className="text-[8px] text-slate-400">B</span>
            <span className="text-sm font-bold text-white">3.2x</span>
          </div>
          <span className="text-[8px] text-slate-500">Ad Set B</span>
        </div>
        <div className="flex flex-col items-center gap-2">
          <div className="w-16 bg-purple-500/20 border border-purple-500/30 rounded-t-lg flex flex-col justify-end p-2" style={{ height: '30%' }}>
            <span className="text-[8px] text-slate-400">C</span>
            <span className="text-sm font-bold text-slate-500">0.9x</span>
          </div>
          <span className="text-[8px] text-red-400">Overlap!</span>
        </div>
      </div>
    </div>
  );
}

function GA4Visual({ colors }) {
  return (
    <div className="h-full flex flex-col justify-between font-mono text-[10px]">
      <div className="flex justify-between items-center text-slate-500 border-b border-white/5 pb-2">
        <span>FUNNEL STAGE</span>
        <span>CONVERSION</span>
      </div>
      <div className="flex-1 flex flex-col justify-center gap-4 mt-2">
        {['Landing', 'Product View', 'Checkout', 'Purchase'].map((stage, i) => (
          <div key={stage} className="flex items-center gap-3">
            <span className="w-20 text-slate-400 text-left">{stage}</span>
            <div className="flex-1 bg-white/5 h-3 rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${100 - i * 20}%` }}
                transition={{ duration: 1, delay: i * 0.2 }}
                className={`h-full bg-gradient-to-r ${colors.gradient} rounded-full`}
              />
            </div>
            <span className={`w-10 text-right ${colors.text} font-semibold`}>
              {100 - i * 20}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function AIVisual({ colors }) {
  return (
    <div className="h-full flex flex-col justify-between font-mono text-[9px] text-cyan-400/80 leading-relaxed">
      <div className="flex justify-between items-center text-slate-500 border-b border-white/5 pb-2">
        <span>SYSTEM LOG</span>
        <span>STATUS: 200 OK</span>
      </div>
      <div className="flex-1 flex flex-col gap-2 mt-3">
        <div>[INFO] GA4 content grouping compiled</div>
        <div>[WARN] Ad Set B overlaps C by 48%</div>
        <div className={`${colors.text} font-bold`}>[ACTION] Apply GSC keywords to FB</div>
        <div className="flex items-center gap-2 mt-2">
          <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
          <span>AI Analysis Complete</span>
        </div>
      </div>
    </div>
  );
}