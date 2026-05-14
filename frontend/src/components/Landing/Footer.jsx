import { FiDatabase } from 'react-icons/fi';

export default function Footer() {
  return (
    <footer className="py-20 px-6 border-t border-white/5 relative overflow-hidden">
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-4xl h-px bg-gradient-to-r from-transparent via-brand-blue/50 to-transparent" />
      
      <div className="max-w-7xl mx-auto flex flex-col items-center">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-5xl font-display font-bold mb-6">讓每一分預算，<br className="sm:hidden" />都成為奪取市場的戰略物資。</h2>
          <button className="bg-white text-black px-10 py-5 rounded-2xl font-bold text-xl shadow-2xl shadow-white/10 hover:scale-105 transition-transform active:scale-95">
            立即建立您的 DataVue 工作區
          </button>
        </div>

        <div className="w-full flex flex-col md:flex-row justify-between items-center gap-10 pt-10 border-t border-white/5">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-brand-blue rounded-lg flex items-center justify-center">
              <FiDatabase className="text-white w-5 h-5" />
            </div>
            <span className="font-display font-bold text-lg text-white">DataVue</span>
          </div>

          <div className="flex flex-wrap justify-center gap-8 text-sm text-slate-500">
            <a href="#" className="hover:text-white transition-colors">文件中心</a>
            <a href="#" className="hover:text-white transition-colors">API 參考手冊</a>
            <a href="#" className="hover:text-white transition-colors">隱私權政策</a>
            <a href="#" className="hover:text-white transition-colors">服務條款</a>
          </div>

          <div className="text-sm text-slate-600 font-mono">
            © 2026 DATAVUE INC. SITE-TEGY READY.
          </div>
        </div>
      </div>
    </footer>
  );
}
