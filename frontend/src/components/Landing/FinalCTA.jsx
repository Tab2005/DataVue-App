import { motion } from 'framer-motion';
import { ArrowRight, Sparkles } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function FinalCTA() {
  const navigate = useNavigate();

  return (
    <section className="relative py-32 px-6 overflow-hidden">
      {/* 背景光暈 */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-slate-900/30 to-transparent" />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[400px] bg-gradient-to-r from-cyan-500/10 via-purple-500/10 to-cyan-500/10 rounded-full blur-[120px]" />

      <div className="max-w-4xl mx-auto relative z-10 text-center">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
        >
          {/* 標籤 */}
          <div className="status-tag mx-auto mb-8">
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
            <span>立即開始</span>
          </div>

          {/* 主標題 */}
          <h2 className="text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-6 leading-tight">
            現在就開始
            <br />
            <span className="gradient-text">讓數據替你工作</span>
          </h2>

          {/* 副標題 */}
          <p className="text-slate-400 text-lg md:text-xl mb-12 max-w-2xl mx-auto leading-relaxed">
            免費連接您的第一個數據源，三分鐘內看到洞察。
            <br />
            無需繁瑣設定，OAuth 安全授權，即刻上手。
          </p>

          {/* CTA 按鈕 */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-10">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => navigate('/login')}
              className="group flex items-center gap-3 px-8 py-4 rounded-full bg-gradient-to-r from-cyan-500 to-purple-500 text-white font-semibold text-base shadow-2xl shadow-cyan-500/25 hover:shadow-cyan-500/40 transition-shadow"
            >
              免費試用
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </motion.button>
            <motion.button
              whileHover={{ x: 4 }}
              onClick={() => document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })}
              className="flex items-center gap-2 px-8 py-4 rounded-full border border-white/10 text-slate-300 hover:text-white hover:border-white/20 transition-all font-medium text-base"
            >
              查看功能示範
            </motion.button>
          </div>

          {/* 信任標語 */}
          <div className="flex items-center justify-center gap-6 text-slate-500 text-sm">
            <span className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-green-400" />
              無需信用卡
            </span>
            <span className="w-px h-4 bg-white/10" />
            <span className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-green-400" />
              OAuth 安全授權
            </span>
            <span className="w-px h-4 bg-white/10" />
            <span className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-green-400" />
              隨時取消
            </span>
          </div>
        </motion.div>
      </div>

      {/* 裝飾邊框線 */}
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />
    </section>
  );
}
