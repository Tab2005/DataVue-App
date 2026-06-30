import { motion } from 'framer-motion';
import { Database, Menu, X } from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function Navbar() {
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <motion.nav
      initial={{ y: -100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
      className="fixed top-0 left-0 right-0 z-50 backdrop-blur-xl bg-black/50 border-b border-white/5"
    >
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        {/* Logo 區 */}
        <div className="flex items-center gap-3 group cursor-pointer" onClick={() => navigate('/')}>
          <div className="relative w-9 h-9">
            <div className="absolute inset-0 rounded-lg bg-gradient-to-tr from-cyan-400 via-purple-500 to-blue-500 opacity-60 blur-sm" />
            <div className="relative w-9 h-9 rounded-lg bg-slate-900 flex items-center justify-center border border-white/10">
              <Database className="w-4 h-4 text-cyan-400" />
            </div>
          </div>
          <span className="font-bold text-lg text-white">
            Data<span className="bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">Vue</span>
          </span>
        </div>

        {/* 桌面端導航連結 */}
        <div className="hidden md:flex items-center gap-8">
          <a href="#features" className="nav-link">核心引擎</a>
          <a href="#solutions" className="nav-link">痛點剖析</a>
          <a href="#andromeda" className="nav-link">AI 引擎</a>
          <a href="#audience" className="nav-link">適用場景</a>
          <a href="#how-it-works" className="nav-link">運作原理</a>
        </div>

        {/* 右側按鈕區 */}
        <div className="hidden md:flex items-center gap-4">
          <button
            onClick={() => navigate('/login')}
            className="text-sm text-slate-400 hover:text-white transition-colors px-4 py-2"
          >
            登入
          </button>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => navigate('/login')}
            className="px-5 py-2 rounded-full bg-gradient-to-r from-cyan-500 to-purple-500 text-white text-sm font-medium shadow-lg shadow-cyan-500/20"
          >
            免費試用
          </motion.button>
        </div>

        {/* 行動端 Menu 按鈕 */}
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="md:hidden p-2"
        >
          {mobileMenuOpen ? <X className="w-6 h-6 text-white" /> : <Menu className="w-6 h-6 text-white" />}
        </button>
      </div>

      {/* 行動端選單 */}
      {mobileMenuOpen && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
          className="md:hidden border-t border-white/5 bg-black/95 backdrop-blur-xl"
        >
          <div className="max-w-7xl mx-auto px-6 py-4 flex flex-col gap-4">
            <a href="#features" onClick={() => setMobileMenuOpen(false)} className="mobile-nav-link">核心引擎</a>
            <a href="#solutions" onClick={() => setMobileMenuOpen(false)} className="mobile-nav-link">痛點剖析</a>
            <a href="#andromeda" onClick={() => setMobileMenuOpen(false)} className="mobile-nav-link">AI 引擎</a>
            <a href="#audience" onClick={() => setMobileMenuOpen(false)} className="mobile-nav-link">適用場景</a>
            <a href="#how-it-works" onClick={() => setMobileMenuOpen(false)} className="mobile-nav-link">運作原理</a>
            <hr className="border-white/10" />
            <button onClick={() => { setMobileMenuOpen(false); navigate('/login'); }} className="mobile-nav-link text-left">登入</button>
            <button onClick={() => { setMobileMenuOpen(false); navigate('/login'); }} className="w-full py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-purple-500 text-white font-medium">
              免費試用
            </button>
          </div>
        </motion.div>
      )}
    </motion.nav>
  );
}