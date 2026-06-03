import { motion } from 'framer-motion';
import { Database, Shield, FileText, Globe } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function Footer() {
  const navigate = useNavigate();

  return (
    <footer className="relative bg-[#040507] border-t border-white/[0.03] pt-24 pb-12 px-6 overflow-hidden">
      {/* 背景裝飾大 Logo - 具有社論的極簡裝飾感 */}
      <div className="absolute -bottom-16 -left-16 font-display font-black text-[12rem] text-white/[0.01] pointer-events-none uppercase select-none">
        DATAVUE
      </div>

      <div className="max-w-7xl mx-auto relative z-10">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-12 mb-16">
          {/* 左側：品牌資訊 */}
          <div className="md:col-span-5 flex flex-col items-start">
            <div className="flex items-center gap-3 mb-6 group cursor-pointer" onClick={() => navigate('/')}>
              <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-brand-blue to-brand-cyan flex items-center justify-center relative overflow-hidden">
                <div className="absolute inset-0.5 bg-black rounded-full flex items-center justify-center">
                  <Database className="text-white w-3.5 h-3.5" />
                </div>
              </div>
              <span className="font-display font-bold text-lg tracking-tight text-white flex items-center">
                Data<span className="font-serif italic font-normal text-slate-300 ml-0.5">Vue</span>
              </span>
            </div>
            
            <p className="text-xs text-slate-500 leading-relaxed font-light max-w-sm mb-6">
              數據的反向工程行銷學。DataVue 幫助企業與個人創作者將跨平台數據熔煉為勝負明確的戰略指令，讓增長不再盲目。
            </p>

            {/* 系統運行狀態 */}
            <div className="flex items-center gap-2 px-3 py-1 rounded-full border border-white/5 bg-[#0a0c10]/40 text-[9px] font-display text-slate-400">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span>ALL SYSTEMS OPERATIONAL</span>
            </div>
          </div>

          {/* 右側：分類導航連結 */}
          <div className="md:col-span-7 grid grid-cols-2 sm:grid-cols-3 gap-8">
            <div>
              <h4 className="text-[10px] font-display font-bold tracking-widest text-slate-400 uppercase mb-4">
                ENGINE CORE
              </h4>
              <ul className="flex flex-col gap-3 text-xs font-light text-slate-500">
                <li><a href="#features" className="hover:text-white transition-colors">功能架構</a></li>
                <li><a href="#solutions" className="hover:text-white transition-colors">盲區剖析</a></li>
                <li><a href="#target" className="hover:text-white transition-colors">決策生態</a></li>
              </ul>
            </div>

            <div>
              <h4 className="text-[10px] font-display font-bold tracking-widest text-slate-400 uppercase mb-4">
                LEGAL & COMPLIANCE
              </h4>
              <ul className="flex flex-col gap-3 text-xs font-light text-slate-500">
                <li className="flex items-center gap-1.5">
                  <Shield className="w-3 h-3 text-brand-cyan" />
                  <a href="#" className="hover:text-white transition-colors">隱私權協議</a>
                </li>
                <li className="flex items-center gap-1.5">
                  <FileText className="w-3 h-3 text-slate-600" />
                  <a href="#" className="hover:text-white transition-colors">服務條款</a>
                </li>
              </ul>
            </div>

            <div>
              <h4 className="text-[10px] font-display font-bold tracking-widest text-slate-400 uppercase mb-4">
                CONNECTIVITY
              </h4>
              <ul className="flex flex-col gap-3 text-xs font-light text-slate-500">
                <li className="flex items-center gap-1.5">
                  <Globe className="w-3 h-3 text-slate-600" />
                  <span className="text-slate-400">繁體中文 (Traditional Chinese)</span>
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* 底部版權宣告與細裝飾線 */}
        <div className="border-t border-white/[0.03] pt-8 flex flex-col sm:flex-row justify-between items-center text-[10px] font-display text-slate-600 font-light">
          <div>
            © {new Date().getFullYear()} DATAVUE. ALL RIGHTS RESERVED.
          </div>
          <div className="mt-4 sm:mt-0 flex gap-4">
            <span>DESIGNED BY THE DATA CANVAS DIVISION</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
