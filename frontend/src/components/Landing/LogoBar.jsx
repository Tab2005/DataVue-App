import { motion } from 'framer-motion';
import { FaFacebook } from 'react-icons/fa';
import { SiGooglecloud } from 'react-icons/si';
import { BarChart3 } from 'lucide-react';

const platforms = [
  { icon: FaFacebook, label: 'Facebook Ads', color: 'text-blue-400', bg: 'bg-blue-500/10', border: 'border-blue-500/20' },
  { icon: SiGooglecloud, label: 'Search Console', color: 'text-green-400', bg: 'bg-green-500/10', border: 'border-green-500/20' },
  { icon: BarChart3, label: 'Google Analytics 4', color: 'text-yellow-400', bg: 'bg-yellow-500/10', border: 'border-yellow-500/20' },
];

const stats = [
  { value: '10,000+', label: '廣告帳戶已連接' },
  { value: '50,000+', label: '份週報自動產出' },
  { value: '3 分鐘', label: '即可看到第一份洞察' },
];

export default function LogoBar() {
  return (
    <section className="relative py-12 px-6 overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-slate-900/20 to-transparent" />
      <div className="absolute inset-0 border-y border-white/[0.04]" />

      <div className="max-w-7xl mx-auto relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
          className="flex flex-col md:flex-row items-center justify-between gap-8"
        >
          {/* 整合平台 */}
          <div className="flex flex-col sm:flex-row items-center gap-4">
            <span className="text-[10px] text-slate-500 uppercase tracking-widest whitespace-nowrap">
              整合平台
            </span>
            <div className="flex items-center gap-3">
              {platforms.map((platform) => (
                <div
                  key={platform.label}
                  className={`flex items-center gap-2 px-4 py-2 rounded-xl border ${platform.bg} ${platform.border} transition-all hover:scale-105`}
                >
                  <platform.icon className={`w-4 h-4 ${platform.color}`} />
                  <span className="text-xs text-slate-400 whitespace-nowrap">{platform.label}</span>
                </div>
              ))}
            </div>
          </div>

          {/* 分隔線 */}
          <div className="hidden md:block w-px h-10 bg-white/5" />

          {/* 數字佐證 */}
          <div className="flex items-center gap-8">
            {stats.map((stat, i) => (
              <div key={i} className="text-center">
                <div className="text-lg font-bold bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">
                  {stat.value}
                </div>
                <div className="text-[10px] text-slate-500 mt-0.5 whitespace-nowrap">{stat.label}</div>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  );
}
