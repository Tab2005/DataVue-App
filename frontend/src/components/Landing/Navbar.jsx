import { motion } from 'framer-motion';
import { Database } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function Navbar() {
  const navigate = useNavigate();

  return (
    <motion.nav 
      initial={{ y: -100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="fixed top-0 left-0 right-0 z-50 px-6 py-4"
    >
      <div className="max-w-7xl mx-auto glass rounded-2xl px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-10 h-10 bg-brand-blue rounded-lg flex items-center justify-center shadow-[0_0_15px_rgba(59,130,246,0.5)]">
            <Database className="text-white w-6 h-6" />
          </div>
          <span className="font-display font-bold text-xl tracking-wider text-white">DataVue</span>
        </div>
        
        <div className="hidden md:flex items-center gap-8">
          <a href="#features" className="text-sm font-medium text-slate-400 hover:text-white transition-colors">功能核心</a>
          <a href="#solutions" className="text-sm font-medium text-slate-400 hover:text-white transition-colors">解決方案</a>
          <a href="#target" className="text-sm font-medium text-slate-400 hover:text-white transition-colors">適用對象</a>
          <a href="#how-it-works" className="text-sm font-medium text-slate-400 hover:text-white transition-colors">運作方式</a>
        </div>

        <div className="flex items-center gap-4">
          <button 
            onClick={() => navigate('/login')}
            className="text-sm font-medium text-white hover:opacity-80 transition-opacity hidden sm:block"
          >
            登入
          </button>
          <button 
            onClick={() => navigate('/login')}
            className="bg-gradient-to-r from-brand-blue to-brand-purple text-white px-5 py-2 rounded-xl text-sm font-semibold shadow-lg shadow-brand-blue/20 hover:scale-105 transition-transform active:scale-95"
          >
            免費體驗
          </button>
        </div>
      </div>
    </motion.nav>
  );
}
