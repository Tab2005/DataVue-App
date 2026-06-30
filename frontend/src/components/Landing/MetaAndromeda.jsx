import { motion } from 'framer-motion';
import { Bot, ClipboardList, Activity, GitBranch, Sliders, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const capabilities = [
  {
    icon: Bot,
    title: '廣告素材評分',
    description: '自動對每支廣告創意進行多維度評分，投放前預測潛力，減少無效預算。',
  },
  {
    icon: ClipboardList,
    title: '審核佇列管理',
    description: '統一管理所有待審廣告素材，支援批次操作，大幅提升代理商的審核效率。',
  },
  {
    icon: Sliders,
    title: '偏差自動校準',
    description: '當評分出現系統性偏差時，自動生成修正版模型，讓評分準確度持續進化。',
  },
  {
    icon: GitBranch,
    title: '版本控制',
    description: '管理不同版本的評分模型，精確掌控上線時機，確保每次更新都有跡可循。',
  },
];

const logLines = [
  { prefix: '[INFO]', text: 'Creative scoring pipeline initialized', color: 'text-slate-400' },
  { prefix: '[SCAN]', text: 'Analyzing 24 ad creatives...', color: 'text-blue-400' },
  { prefix: '[SCORE]', text: 'Creative #A1: 87/100 — HIGH POTENTIAL', color: 'text-cyan-400' },
  { prefix: '[SCORE]', text: 'Creative #A2: 41/100 — review required', color: 'text-yellow-400' },
  { prefix: '[DRIFT]', text: 'Calibration dataset synced (n=312)', color: 'text-purple-400' },
  { prefix: '[OK]', text: 'Profile v2.4 promoted to production', color: 'text-teal-400' },
];

export default function MetaAndromeda() {
  const navigate = useNavigate();

  return (
    <section id="andromeda" className="relative py-32 px-6 overflow-hidden">
      {/* 背景裝飾 */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-slate-900/40 to-transparent" />
      <div className="absolute top-1/2 right-0 w-[500px] h-[500px] bg-purple-500/5 rounded-full blur-[150px] -translate-y-1/2" />
      <div className="absolute top-1/2 left-0 w-[400px] h-[400px] bg-cyan-500/5 rounded-full blur-[150px] -translate-y-1/2" />

      <div className="max-w-7xl mx-auto relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">

          {/* 左側：文案 */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
            className="lg:col-span-5"
          >
            {/* 標籤 */}
            <div className="flex items-center gap-3 mb-6">
              <div className="status-tag">
                <Bot className="w-3.5 h-3.5 text-purple-400" />
                <span>AI 廣告引擎</span>
              </div>
              <span className="px-3 py-1 rounded-full border border-orange-500/30 bg-orange-500/10 text-orange-400 text-[10px] font-semibold uppercase tracking-wider">
                Coming Soon
              </span>
            </div>

            {/* 主標題 */}
            <h2 className="section-title mb-4">
              Meta Andromeda
              <br />
              <span className="bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">
                AI 廣告評分引擎
              </span>
            </h2>

            {/* 說明 */}
            <p className="text-slate-400 text-base leading-relaxed mb-10">
              每一支廣告在投放前，都經過 AI 的嚴格審核。
              廣告素材評分、自動審核佇列、偏差校準 — 為代理商量身設計的智能廣告管理系統，讓每一分預算都花在刀口上。
            </p>

            {/* 能力卡片 */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-10">
              {capabilities.map((cap, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: i * 0.1 }}
                  className="p-4 rounded-2xl border border-white/5 bg-slate-900/50 hover:border-purple-500/20 hover:bg-purple-500/5 transition-all duration-300 group"
                >
                  <div className="w-8 h-8 rounded-lg bg-purple-500/10 border border-purple-500/20 flex items-center justify-center mb-3 group-hover:bg-purple-500/20 transition-colors">
                    <cap.icon className="w-4 h-4 text-purple-400" />
                  </div>
                  <h4 className="text-sm font-semibold text-white mb-1">{cap.title}</h4>
                  <p className="text-xs text-slate-500 leading-relaxed">{cap.description}</p>
                </motion.div>
              ))}
            </div>

            {/* CTA */}
            <div className="flex items-center gap-4">
              <motion.button
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.97 }}
                onClick={() => navigate('/login')}
                className="group flex items-center gap-2 px-6 py-3 rounded-full bg-gradient-to-r from-purple-500 to-cyan-500 text-white text-sm font-semibold shadow-lg shadow-purple-500/20"
              >
                申請優先體驗
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </motion.button>
              <span className="text-xs text-slate-500">特別為代理商夥伴開放早期測試</span>
            </div>
          </motion.div>

          {/* 右側：仿終端機視覺 */}
          <motion.div
            initial={{ opacity: 0, x: 30 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="lg:col-span-7"
          >
            <div className="relative rounded-3xl border border-purple-500/20 bg-slate-950/80 backdrop-blur-xl overflow-hidden shadow-2xl shadow-purple-500/10">
              {/* 終端機頂部 Bar */}
              <div className="flex items-center gap-3 px-5 py-4 border-b border-white/5 bg-black/30">
                <div className="flex gap-2">
                  <div className="w-3 h-3 rounded-full bg-red-500/60" />
                  <div className="w-3 h-3 rounded-full bg-yellow-500/60" />
                  <div className="w-3 h-3 rounded-full bg-green-500/60" />
                </div>
                <span className="text-slate-500 text-xs font-mono ml-2">andromeda — scoring-pipeline</span>
                <div className="ml-auto flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
                  <span className="text-[10px] text-green-400 font-mono">ACTIVE</span>
                </div>
              </div>

              {/* Log 輸出 */}
              <div className="p-6 font-mono text-[11px] leading-relaxed space-y-2 min-h-[220px]">
                {logLines.map((line, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -10 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.4, delay: 0.4 + i * 0.12 }}
                    className="flex items-start gap-3"
                  >
                    <span className={`shrink-0 font-bold ${line.color}`}>{line.prefix}</span>
                    <span className="text-slate-400">{line.text}</span>
                  </motion.div>
                ))}
                {/* 游標閃爍 */}
                <div className="flex items-center gap-3 mt-2">
                  <span className="text-purple-400 font-bold">{'>'}</span>
                  <motion.span
                    animate={{ opacity: [1, 0, 1] }}
                    transition={{ duration: 1, repeat: Infinity }}
                    className="w-2 h-4 bg-purple-400/60 rounded-sm"
                  />
                </div>
              </div>

              {/* 底部統計 */}
              <div className="px-6 py-4 border-t border-white/5 bg-black/20 grid grid-cols-3 gap-4">
                {[
                  { label: '已評估素材', value: '1,248' },
                  { label: '平均評分', value: '74.2' },
                  { label: '校準準確率', value: '91.6%' },
                ].map((stat, i) => (
                  <div key={i} className="text-center">
                    <div className="text-lg font-bold text-purple-400">{stat.value}</div>
                    <div className="text-[10px] text-slate-500 mt-0.5">{stat.label}</div>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
