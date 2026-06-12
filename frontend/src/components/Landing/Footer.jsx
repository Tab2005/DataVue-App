import { motion } from 'framer-motion';
import { Database, Shield, FileText, Globe, Zap } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function Footer() {
  const navigate = useNavigate();

  return (
    <footer className="relative bg-slate-950 border-t border-white/5 pt-20 pb-8 px-6 overflow-hidden">
      {/* 背景裝飾 Logo */}
      <div className="absolute -bottom-8 -left-8 font-bold text-[10rem] text-white/[0.02] pointer-events-none select-none leading-none">
        DATAVUE
      </div>

      <div className="max-w-7xl mx-auto relative z-10">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-12 mb-16">
          {/* 左側：品牌資訊 */}
          <div className="md:col-span-5 flex flex-col items-start">
            <div className="flex items-center gap-3 mb-6 cursor-pointer group" onClick={() => navigate('/')}>
              <div className="relative w-10 h-10">
                <div className="absolute inset-0 rounded-xl bg-gradient-to-tr from-cyan-500 to-purple-500 opacity-50 blur-sm" />
                <div className="relative w-10 h-10 rounded-xl bg-gradient-to-br from-slate-900 to-black flex items-center justify-center border border-white/10">
                  <Database className="w-5 h-5 text-cyan-400" />
                </div>
              </div>
              <span className="font-bold text-xl tracking-tight text-white">
                Data<span className="font-serif italic font-light bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">Vue</span>
              </span>
            </div>

            <p className="text-xs text-slate-500 leading-relaxed max-w-sm mb-6">
              匯聚所有行銷數據，以 AI 為核心提煉洞察。讓每一次決策都建立在清晰的數據基礎之上。
            </p>

            {/* 系統運行狀態 */}
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full border border-emerald-500/20 bg-emerald-500/5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-[10px] text-emerald-400 font-medium uppercase tracking-wider">
                All Systems Operational
              </span>
            </div>
          </div>

          {/* 右側：連結分類 */}
          <div className="md:col-span-7 grid grid-cols-2 sm:grid-cols-3 gap-8">
            <div>
              <h4 className="text-[10px] font-semibold uppercase tracking-widest text-slate-500 mb-4 flex items-center gap-2">
                <Zap className="w-3 h-3 text-cyan-400" />
                核心功能
              </h4>
              <ul className="space-y-3 text-xs text-slate-500">
                <li><a href="#features" className="hover:text-white transition-colors">功能介紹</a></li>
                <li><a href="#solutions" className="hover:text-white transition-colors">痛點剖析</a></li>
                <li><a href="#audience" className="hover:text-white transition-colors">適用場景</a></li>
                <li><a href="#how-it-works" className="hover:text-white transition-colors">運作原理</a></li>
              </ul>
            </div>

            <div>
              <h4 className="text-[10px] font-semibold uppercase tracking-widest text-slate-500 mb-4 flex items-center gap-2">
                <Shield className="w-3 h-3 text-purple-400" />
                法律資訊
              </h4>
              <ul className="space-y-3 text-xs text-slate-500">
                <li>
                  <a href="#" className="hover:text-white transition-colors flex items-center gap-1.5">
                    <FileText className="w-3 h-3 text-slate-600" />
                    隱私權政策
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-white transition-colors flex items-center gap-1.5">
                    <FileText className="w-3 h-3 text-slate-600" />
                    服務條款
                  </a>
                </li>
              </ul>
            </div>

            <div>
              <h4 className="text-[10px] font-semibold uppercase tracking-widest text-slate-500 mb-4 flex items-center gap-2">
                <Globe className="w-3 h-3 text-blue-400" />
                語言與地區
              </h4>
              <ul className="space-y-3 text-xs text-slate-500">
                <li className="flex items-center gap-1.5">
                  <Globe className="w-3 h-3 text-slate-600" />
                  繁體中文
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* 底部版權 */}
        <div className="border-t border-white/5 pt-8 flex flex-col sm:flex-row justify-between items-center text-[10px] text-slate-600">
          <div>
            © {new Date().getFullYear()} DATAVUE. ALL RIGHTS RESERVED.
          </div>
          <div className="mt-4 sm:mt-0 flex items-center gap-2">
            <span>Built with</span>
            <span className="text-cyan-400">◆</span>
            <span>DataVue Engine</span>
          </div>
        </div>
      </div>
    </footer>
  );
}