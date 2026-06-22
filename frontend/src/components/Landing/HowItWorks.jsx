import { motion } from 'framer-motion';
import { Link2, Workflow, Sparkles, KeyRound, Cpu, Rocket } from 'lucide-react';

const steps = [
  {
    num: '01',
    icon: KeyRound,
    title: '連接數據源',
    subtitle: '一鍵授權，極速串接',
    description: '透過 Google 與 Facebook 官方 OAuth 2.0 授權，點擊即可完成串接。我們採用加密機制確保您的資料安全。',
    color: 'blue'
  },
  {
    num: '02',
    icon: Cpu,
    title: 'AI 智能熔煉',
    subtitle: '多源數據自動整合',
    description: '系統自動執行數據清洗、去噪與關聯性建模。GA4、FB Ads、GSC 在這一階段被整合成單一視圖。',
    color: 'purple'
  },
  {
    num: '03',
    icon: Rocket,
    title: '獲取行動洞察',
    subtitle: 'AI 驅動的策略建議',
    description: '獲得每週數據解譯報告與可執行的優化方案。告別面對數字的焦慮，以清晰的洞察搶佔先機。',
    color: 'cyan'
  }
];

const colorMap = {
  blue: { from: 'from-blue-500', to: 'to-cyan-500', text: 'text-blue-400', bg: 'bg-blue-500/10', border: 'border-blue-500/30', glow: 'shadow-blue-500/20' },
  purple: { from: 'from-purple-500', to: 'to-pink-500', text: 'text-purple-400', bg: 'bg-purple-500/10', border: 'border-purple-500/30', glow: 'shadow-purple-500/20' },
  cyan: { from: 'from-cyan-500', to: 'to-teal-500', text: 'text-cyan-400', bg: 'bg-cyan-500/10', border: 'border-cyan-500/30', glow: 'shadow-cyan-500/20' }
};

export default function HowItWorks() {
  return (
    <section id="how-it-works" className="relative py-32 px-6 overflow-hidden">
      {/* 背景裝飾 */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-slate-950/50 to-transparent" />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[300px] bg-gradient-to-r from-cyan-500/5 via-purple-500/5 to-blue-500/5 rounded-full blur-[150px]" />

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
            <Workflow className="w-3.5 h-3.5 text-cyan-400" />
            <span>運作原理</span>
          </div>
          <h2 className="section-title mb-4">
            三步驟開啟
            <br />
            <span className="gradient-text">數據驅動增長</span>
          </h2>
          <p className="section-subtitle max-w-2xl mx-auto">
            從數據混亂到決策清晰，只需幾分鐘的熔煉過程。
          </p>
        </motion.div>

        {/* 步驟卡片 */}
        <div className="relative">
          {/* 連接線裝飾 (Desktop) */}
          <div className="hidden lg:block absolute top-1/2 left-[16.67%] right-[16.67%] h-[2px] -translate-y-1/2 -z-10">
            <div className="h-full bg-gradient-to-r from-blue-500/30 via-purple-500/30 to-cyan-500/30 rounded-full" />
            <div className="absolute inset-0 bg-gradient-to-r from-blue-500 via-purple-500 to-cyan-500 opacity-30 blur-sm" />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {steps.map((step, index) => {
              const colors = colorMap[step.color];
              return (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 40 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.8, delay: index * 0.15 }}
                  className="group relative"
                >
                  {/* 卡片本體 */}
                  <div className={`
                    relative rounded-3xl border border-white/5
                    bg-gradient-to-br from-slate-900/80 to-slate-950/80
                    backdrop-blur-xl p-8
                    hover:border-white/10 transition-all duration-500
                    hover:shadow-2xl ${colors.glow}
                  `}>
                    {/* 背景光暈 */}
                    <div className={`absolute -top-20 -right-20 w-40 h-40 bg-gradient-to-br ${colors.from} to-transparent rounded-full blur-[80px] opacity-0 group-hover:opacity-30 transition-opacity duration-700`} />

                    {/* 步驟編號 */}
                    <div className="absolute top-6 right-6 font-mono text-4xl font-bold text-slate-800 group-hover:text-slate-700 transition-colors">
                      {step.num}
                    </div>

                    {/* 圖標容器 */}
                    <div className="relative w-16 h-16 mb-8">
                      <div className={`absolute inset-0 bg-gradient-to-br ${colors.from} ${colors.to} rounded-2xl blur-sm opacity-50 group-hover:opacity-70 transition-opacity`} />
                      <div className={`relative w-16 h-16 rounded-2xl bg-gradient-to-br ${colors.from} ${colors.to} flex items-center justify-center border border-white/10 group-hover:scale-110 transition-transform duration-300`}>
                        <step.icon className="w-7 h-7 text-white" />
                      </div>
                      {/* 連接線端點 */}
                      <div className={`absolute -right-[calc(100%+1rem)] top-1/2 -translate-y-1/2 w-4 h-4 rounded-full bg-gradient-to-br ${colors.from} ${colors.to} opacity-0 lg:group-hover:opacity-100 transition-opacity hidden lg:block`} />
                    </div>

                    {/* 內容 */}
                    <h3 className="text-xl font-bold text-white mb-2">
                      {step.title}
                    </h3>
                    <span className={`text-xs ${colors.text} uppercase tracking-wider`}>
                      {step.subtitle}
                    </span>
                    <p className="text-sm text-slate-500 leading-relaxed mt-4">
                      {step.description}
                    </p>

                    {/* 底部指示箭頭 (非最後一個) */}
                    {index < steps.length - 1 && (
                      <div className="hidden lg:flex absolute -right-4 top-1/2 -translate-y-1/2 w-8 h-8 items-center justify-center text-slate-600">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </div>
                    )}
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}