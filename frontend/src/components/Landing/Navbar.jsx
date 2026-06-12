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
      className="fixed top-0 left-0 right-0 z-50 px-6 py-5"
    >
      <div className="max-w-7xl mx-auto glass-panel rounded-2xl px-6 py-3.5 flex items-center justify-between border border-white/[0.08] bg-black/60 backdrop-blur-2xl">
        {/* Logo 區 */}
        <div className="flex items-center gap-3 group cursor-pointer" onClick={() => navigate('/')}>
          <div className="relative w-10 h-10">
            {/* 外層光環 */}
            <div className="absolute inset-0 rounded-xl bg-gradient-to-tr from-cyan-400 via-purple-500 to-blue-500 opacity-50 blur-sm animate-pulse" />
            {/* 主體 */}
            <div className="relative w-10 h-10 rounded-xl bg-gradient-to-br from-slate-900 via-slate-800 to-black flex items-center justify-center border border-white/10 overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-tr from-cyan-500/10 to-purple-500/10" />
              <Database className="text-cyan-400 w-5 h-5 group-hover:rotate-12 transition-transform duration-300 relative z-10" />
            </div>
          </div>
          <span className="font-display font-bold text-xl tracking-tight text-white">
            Data<span className="font-serif italic font-light bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">Vue</span>
          </span>
        </div>

        {/* 桌面端導航連結 */}
        <div className="hidden md:flex items-center gap-10">
          <a href="#features" className="nav-link">
            核心引擎
          </a>
          <a href="#solutions" className="nav-link">
            痛點剖析
          </a>
          <a href="#audience" className="nav-link">
            適用場景
          </a>
          <a href="#how-it-works" className="nav-link">
            運作原理
          </a>
        </div>

        {/* 右側按鈕區 */}
        <div className="hidden md:flex items-center gap-4">
          <button
            onClick={() => navigate('/login')}
            className="text-sm font-medium text-slate-400 hover:text-white transition-colors duration-300 px-4 py-2"
          >
            登入
          </button>
          <motion.button
            whileHover={{ scale: 1.02, boxShadow: '0 0 30px rgba(6, 182, 212, 0.3)' }}
            whileTap={{ scale: 0.98 }}
            onClick={() => navigate('/login')}
            className="px-6 py-2.5 rounded-full bg-gradient-to-r from-cyan-500 to-purple-500 text-white font-semibold text-sm tracking-wide transition-all duration-300 shadow-lg shadow-cyan-500/20"
          >
            立即開始
          </motion.button>
        </div>

        {/* 行動端 Menu 按鈕 */}
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="md:hidden text-white hover:text-cyan-400 transition-colors p-2"
        >
          {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      {/* 行動端選單 */}
      {mobileMenuOpen && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          className="absolute top-full left-6 right-6 mt-3 glass-panel p-6 border border-white/[0.08] bg-black/90 backdrop-blur-2xl rounded-2xl flex flex-col gap-5 md:hidden"
        >
          <a href="#features" onClick={() => setMobileMenuOpen(false)} className="mobile-nav-link">核心引擎</a>
          <a href="#solutions" onClick={() => setMobileMenuOpen(false)} className="mobile-nav-link">痛點剖析</a>
          <a href="#audience" onClick={() => setMobileMenuOpen(false)} className="mobile-nav-link">適用場景</a>
          <a href="#how-it-works" onClick={() => setMobileMenuOpen(false)} className="mobile-nav-link">運作原理</a>
          <hr className="border-white/10 my-2" />
          <button onClick={() => { setMobileMenuOpen(false); navigate('/login'); }} className="mobile-nav-link text-left text-cyan-400">登入</button>
          <button onClick={() => { setMobileMenuOpen(false); navigate('/login'); }} className="w-full py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-purple-500 text-white font-semibold text-sm">
            立即開始
          </button>
        </motion.div>
      )}
    </motion.nav>
  );
}