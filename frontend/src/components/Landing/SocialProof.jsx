import { motion } from 'framer-motion';
import { Quote } from 'lucide-react';

const testimonials = [
  {
    quote: '使用 DataVue 之後，每週的廣告報告從 3 小時縮短到不到 20 分鐘。自動排程週報功能讓我可以把時間花在策略上，而不是整理數字。',
    name: 'Vivian L.',
    role: '行銷經理',
    company: '電商品牌',
    color: 'cyan',
    metric: { value: '-85%', label: '報表整理時間' }
  },
  {
    quote: 'GSC 的關鍵字缺口分析幫我們找到競品沒有覆蓋的長尾詞。這在以前需要付費工具才能做到，現在全部整合在同一個介面。',
    name: 'Jason C.',
    role: 'SEO 策略師',
    company: '數位代理商',
    color: 'purple',
    metric: { value: '+40%', label: '自然流量成長' }
  },
  {
    quote: '同時服務 12 個客戶，DataVue 的多帳號切換和團隊協作功能是我們代理商的剛需。現在每個客戶的週報都是自動生成的。',
    name: 'Michelle W.',
    role: '業務總監',
    company: '整合行銷公司',
    color: 'blue',
    metric: { value: '12x', label: '客戶帳號管理' }
  },
];

const colorMap = {
  cyan: { border: 'border-cyan-500/15', glow: 'hover:border-cyan-500/30 hover:shadow-cyan-500/10', quote: 'text-cyan-500/30', metric: 'text-cyan-400', badge: 'bg-cyan-500/10 border-cyan-500/20' },
  purple: { border: 'border-purple-500/15', glow: 'hover:border-purple-500/30 hover:shadow-purple-500/10', quote: 'text-purple-500/30', metric: 'text-purple-400', badge: 'bg-purple-500/10 border-purple-500/20' },
  blue: { border: 'border-blue-500/15', glow: 'hover:border-blue-500/30 hover:shadow-blue-500/10', quote: 'text-blue-500/30', metric: 'text-blue-400', badge: 'bg-blue-500/10 border-blue-500/20' },
};

export default function SocialProof() {
  return (
    <section className="relative py-24 px-6 overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-slate-900/20 to-transparent" />

      <div className="max-w-7xl mx-auto relative z-10">
        {/* 標題 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
          className="text-center mb-14"
        >
          <p className="text-[10px] text-slate-500 uppercase tracking-widest mb-3">使用者回饋</p>
          <h2 className="text-2xl md:text-3xl font-bold text-white">
            他們已經用數據
            <span className="bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">贏得先機</span>
          </h2>
        </motion.div>

        {/* 評語卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {testimonials.map((t, i) => {
            const colors = colorMap[t.color];
            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: i * 0.12 }}
                className={`group relative rounded-2xl border ${colors.border} ${colors.glow} bg-slate-900/40 backdrop-blur-sm p-7 transition-all duration-500 hover:shadow-xl flex flex-col`}
              >
                {/* 大引號裝飾 */}
                <Quote className={`w-8 h-8 ${colors.quote} mb-4 shrink-0`} />

                {/* 引文 */}
                <p className="text-sm text-slate-400 leading-relaxed flex-1 mb-6">
                  {t.quote}
                </p>

                {/* 成效數字 */}
                <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full border ${colors.badge} mb-5 self-start`}>
                  <span className={`text-base font-bold ${colors.metric}`}>{t.metric.value}</span>
                  <span className="text-[10px] text-slate-500">{t.metric.label}</span>
                </div>

                {/* 用戶資訊 */}
                <div className="flex items-center gap-3 pt-5 border-t border-white/5">
                  <div className={`w-8 h-8 rounded-full border ${colors.badge} flex items-center justify-center text-xs font-bold ${colors.metric}`}>
                    {t.name[0]}
                  </div>
                  <div>
                    <div className="text-xs font-semibold text-white">{t.name}</div>
                    <div className="text-[10px] text-slate-500">{t.role} · {t.company}</div>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
