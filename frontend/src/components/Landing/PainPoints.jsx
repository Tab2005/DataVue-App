import { motion } from 'framer-motion';
import { AlertTriangle, Lightbulb, Cpu, Layers } from 'lucide-react';

const painPoints = [
  {
    num: '01',
    icon: Layers,
    problem: '每天在 GA4、Facebook Ads、Search Console 之間來回切換，在破碎的分頁中手動拼湊數據真相。',
    solution: '一站式數據熔煉。所有平台指標在同一空間對齊與編排，一眼洞悉大局。',
    color: 'blue'
  },
  {
    num: '02',
    icon: AlertTriangle,
    problem: '看著密密麻麻的圖表與數字，卻無法回答：「今天我的下一個動作該是什麼？」',
    solution: 'AI 戰略導航。結合多源數據，自動產出明確、可操作且具備商業勝負感的決策建議。',
    color: 'purple'
  },
  {
    num: '03',
    icon: Cpu,
    problem: '當需要新增指標或進行自定義內容分組時，受限於傳統報表的僵化架構，難以敏捷調整。',
    solution: '模組化積木架構。自訂內容分組、報表自動排程，高度靈活的數據源配置，隨您的行銷規模共同成長。',
    color: 'cyan'
  }
];

const colorMap = {
  blue: { from: 'from-blue-500', to: 'to-cyan-500', text: 'text-blue-400', bg: 'bg-blue-500/10', border: 'border-blue-500/20' },
  purple: { from: 'from-purple-500', to: 'to-pink-500', text: 'text-purple-400', bg: 'bg-purple-500/10', border: 'border-purple-500/20' },
  cyan: { from: 'from-cyan-500', to: 'to-teal-500', text: 'text-cyan-400', bg: 'bg-cyan-500/10', border: 'border-cyan-500/20' }
};

export default function PainPoints() {
  return (
    <section id="solutions" className="relative py-32 px-6 overflow-hidden bg-gradient-to-b from-slate-950/50 via-slate-900/30 to-transparent">
      {/* 裝飾線 */}
      <div className="absolute top-0 left-1/4 w-[1px] h-full bg-gradient-to-b from-cyan-500/20 via-transparent to-transparent hidden lg:block" />
      <div className="absolute top-0 right-1/4 w-[1px] h-full bg-gradient-to-b from-purple-500/20 via-transparent to-transparent hidden lg:block" />

      <div className="max-w-7xl mx-auto relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-16">
          {/* 左側：標題區 */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
            className="lg:col-span-4 flex flex-col justify-start lg:sticky lg:top-36 h-fit"
          >
            <div className="status-tag mb-6">
              <AlertTriangle className="w-3.5 h-3.5 text-purple-400" />
              <span>常見痛點</span>
            </div>
            <h2 className="section-title mb-6">
              行銷數據的
              <br />
              <span className="gradient-text">三大盲區</span>
            </h2>
            <p className="text-slate-500 leading-relaxed text-sm">
              我們懂行銷人與決策者的焦慮。混亂的數據不是資產，而是決策的噪音。
              DataVue 旨在終結這種無序，將冰冷的數字鑄造成進攻市場的利刃。
            </p>
          </motion.div>

          {/* 右側：痛點卡片 */}
          <div className="lg:col-span-8 flex flex-col gap-6">
            {painPoints.map((item, index) => {
              const colors = colorMap[item.color];
              return (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.8, delay: index * 0.1 }}
                  className={`
                    group relative rounded-3xl border border-white/5
                    bg-gradient-to-br from-slate-900/60 to-slate-950/60
                    backdrop-blur-xl p-8 lg:p-10
                    hover:border-white/10 transition-all duration-500
                    hover:shadow-2xl hover:shadow-black/20
                  `}
                >
                  {/* 右上角光暈 */}
                  <div className={`absolute top-0 right-0 w-40 h-40 bg-gradient-to-tr ${colors.from} to-transparent rounded-full blur-[100px] opacity-0 group-hover:opacity-20 transition-opacity duration-700`} />

                  <div className="flex flex-col md:flex-row gap-8 relative z-10">
                    {/* 序號區 */}
                    <div className="flex flex-row md:flex-col items-center md:items-start gap-4">
                      <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${colors.from} ${colors.to} flex items-center justify-center shadow-lg`}>
                        <item.icon className="w-6 h-6 text-white" />
                      </div>
                      <span className="font-mono text-4xl md:text-5xl font-bold text-slate-800 group-hover:text-slate-600 transition-colors">
                        {item.num}
                      </span>
                    </div>

                    {/* 內容區 */}
                    <div className="flex-1 space-y-6">
                      <h3 className="text-lg lg:text-xl font-semibold text-white">
                        {index === 0 && '多平台迷航 (Platform Fragmentation)'}
                        {index === 1 && '資訊過載卻無洞察 (Metrics Without Insights)'}
                        {index === 2 && '架構僵化難擴展 (Brittle Data Structures)'}
                      </h3>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 border-t border-white/5">
                        {/* 痛點 */}
                        <div className="space-y-2">
                          <div className={`flex items-center gap-2 text-[10px] font-semibold uppercase tracking-widest ${colors.text}`}>
                            <AlertTriangle className="w-3 h-3" />
                            現狀之痛
                          </div>
                          <p className="text-sm text-slate-500 leading-relaxed group-hover:text-slate-400 transition-colors">
                            {item.problem}
                          </p>
                        </div>

                        {/* 解決方案 */}
                        <div className="space-y-2 md:border-l md:border-white/5 md:pl-6">
                          <div className={`flex items-center gap-2 text-[10px] font-semibold uppercase tracking-widest text-cyan-400`}>
                            <Lightbulb className="w-3 h-3" />
                            DataVue 方案
                          </div>
                          <p className="text-sm text-slate-300 leading-relaxed group-hover:text-white transition-colors">
                            {item.solution}
                          </p>
                        </div>
                      </div>
                    </div>
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