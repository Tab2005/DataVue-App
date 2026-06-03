import { motion } from 'framer-motion';
import { Database, Menu, X } from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function Navbar() {
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <motion.nav 
      initial={{ y: -50, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
      className="fixed top-0 left-0 right-0 z-50 px-6 py-6"
    >
      <div className="max-w-7xl mx-auto glass-panel rounded-full px-8 py-3 flex items-center justify-between border border-white/[0.03] bg-black/40 backdrop-blur-xl">
        {/* Logo 區 - 使用 Fraunces Serif 字體營造高雅社論感 */}
        <div className="flex items-center gap-3 group cursor-pointer" onClick={() => navigate('/')}>
          <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-brand-blue via-brand-purple to-brand-cyan flex items-center justify-center relative overflow-hidden">
            <div className="absolute inset-0.5 bg-black rounded-full flex items-center justify-center">
              <Database className="text-white w-4 h-4 group-hover:rotate-12 transition-transform duration-300" />
            </div>
            {/* 動態光環 */}
            <div className="absolute inset-0 bg-white/20 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
          </div>
          <span className="font-display font-bold text-xl tracking-tight text-white flex items-center">
            Data<span className="font-serif italic font-normal text-slate-300 ml-0.5">Vue</span>
          </span>
        </div>
        
        {/* 桌面端導航連結 */}
        <div className="hidden md:flex items-center gap-8">
          <a href="#features" className="text-xs tracking-widest uppercase font-display text-slate-400 hover:text-white transition-colors duration-300 relative group py-1">
            核心引擎
            <span className="absolute bottom-0 left-0 w-0 h-[1px] bg-white group-hover:w-full transition-all duration-300" />
          </a>
          <a href="#solutions" className="text-xs tracking-widest uppercase font-display text-slate-400 hover:text-white transition-colors duration-300 relative group py-1">
            盲區剖析
            <span className="absolute bottom-0 left-0 w-0 h-[1px] bg-white group-hover:w-full transition-all duration-300" />
          </a>
          <a href="#target" className="text-xs tracking-widest uppercase font-display text-slate-400 hover:text-white transition-colors duration-300 relative group py-1">
            共鳴生態
            <span className="absolute bottom-0 left-0 w-0 h-[1px] bg-white group-hover:w-full transition-all duration-300" />
          </a>
          <a href="#how-it-works" className="text-xs tracking-widest uppercase font-display text-slate-400 hover:text-white transition-colors duration-300 relative group py-1">
            三步熔煉
            <span className="absolute bottom-0 left-0 w-0 h-[1px] bg-white group-hover:w-full transition-all duration-300" />
          </a>
        </div>

        {/* 右側按鈕區 - 去除大橘色，改用精緻的白金/黑曜石配色 */}
        <div className="hidden md:flex items-center gap-6">
          <button 
            onClick={() => navigate('/login')}
            className="text-xs uppercase tracking-widest font-display font-medium text-slate-400 hover:text-white transition-colors duration-300"
          >
            登入平台
          </button>
          <motion.button 
            whileHover={{ scale: 1.02, borderColor: 'rgba(255,255,255,0.3)' }}
            whileTap={{ scale: 0.98 }}
            onClick={() => navigate('/login')}
            className="px-6 py-2.5 rounded-full border border-white/10 bg-white text-black font-display font-semibold text-xs tracking-wider uppercase transition-all duration-300 shadow-[0_4px_20px_rgba(255,255,255,0.08)] hover:shadow-[0_4px_30px_rgba(255,255,255,0.15)]"
          >
            免費體驗
          </motion.button>
        </div>

        {/* 行動端 Menu 按鈕 */}
        <button 
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="md:hidden text-white hover:text-slate-300 transition-colors"
        >
          {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      {/* 行動端選單 */}
      {mobileMenuOpen && (
        <motion.div 
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          className="absolute top-full left-6 right-6 mt-2 glass p-6 border border-white/[0.05] bg-black/90 backdrop-blur-2xl flex flex-col gap-6 md:hidden"
        >
          <a 
            href="#features" 
            onClick={() => setMobileMenuOpen(false)}
            className="text-sm font-medium text-slate-300 hover:text-white"
          >
            核心引擎
          </a>
          <a 
            href="#solutions" 
            onClick={() => setMobileMenuOpen(false)}
            className="text-sm font-medium text-slate-300 hover:text-white"
          >
            盲區剖析
          </a>
          <a 
            href="#target" 
            onClick={() => setMobileMenuOpen(false)}
            className="text-sm font-medium text-slate-300 hover:text-white"
          >
            共鳴生態
          </a>
          <a 
            href="#how-it-works" 
            onClick={() => setMobileMenuOpen(false)}
            className="text-sm font-medium text-slate-300 hover:text-white"
          >
            三步熔煉
          </a>
          <hr className="border-white/10" />
          <div className="flex flex-col gap-4">
            <button 
              onClick={() => { setMobileMenuOpen(false); navigate('/login'); }}
              className="text-sm font-medium text-slate-300 hover:text-white py-2 text-center"
            >
              登入平台
            </button>
            <button 
              onClick={() => { setMobileMenuOpen(false); navigate('/login'); }}
              className="bg-white text-black py-3 rounded-xl text-sm font-semibold text-center"
            >
              免費體驗
            </button>
          </div>
        </motion.div>
      )}
    </motion.nav>
  );
}
