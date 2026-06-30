import { motion, AnimatePresence } from 'framer-motion';
import { Database, Shield, FileText, Globe, Zap, ChevronDown } from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const faqs = [
  {
    q: '需要信用卡才能試用嗎？',
    a: '不需要。您可以免費連接第一個數據源並開始使用，無需綁定任何付款方式。'
  },
  {
    q: '支援哪些廣告帳戶與平台？',
    a: 'DataVue 目前整合 Facebook Ads、Google Search Console（GSC）與 Google Analytics 4（GA4），透過官方 OAuth 2.0 授權連接。'
  },
  {
    q: '我的數據安全嗎？',
    a: '是的。我們使用 OAuth 2.0 官方授權流程，不會儲存您的帳號密碼。所有數據傳輸皆經過加密，且不會與第三方共享。'
  },
  {
    q: '是否支援多人協作與多帳號管理？',
    a: '支援。DataVue 提供完整的團隊功能，可邀請成員並設定不同的存取權限，適合代理商同時管理多個客戶帳號。'
  },
  {
    q: 'Meta Andromeda AI 引擎什麼時候開放？',
    a: 'Meta Andromeda 目前正在開放早期測試，歡迎代理商夥伴申請優先體驗。您可以點選頁面中的「申請優先體驗」按鈕加入等候名單。'
  },
];

function FAQItem({ item, isOpen, onToggle }) {
  return (
    <div className="border-b border-white/5 last:border-0">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between py-5 text-left group"
      >
        <span className="text-sm text-slate-300 group-hover:text-white transition-colors pr-8">
          {item.q}
        </span>
        <ChevronDown className={`w-4 h-4 text-slate-500 shrink-0 transition-transform duration-300 ${isOpen ? 'rotate-180' : ''}`} />
      </button>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
            className="overflow-hidden"
          >
            <p className="text-sm text-slate-500 leading-relaxed pb-5 pr-8">
              {item.a}
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default function Footer() {
  const navigate = useNavigate();
  const [openFaq, setOpenFaq] = useState(null);

  return (
    <footer className="relative bg-slate-950 border-t border-white/5 pt-20 pb-8 px-6 overflow-hidden">
      {/* 背景裝飾 Logo */}
      <div className="absolute -bottom-8 -left-8 font-bold text-[10rem] text-white/[0.02] pointer-events-none select-none leading-none">
        DATAVUE
      </div>

      <div className="max-w-7xl mx-auto relative z-10">
        {/* FAQ 區塊 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
          className="mb-20"
        >
          <div className="text-center mb-10">
            <h3 className="text-2xl font-bold text-white mb-2">常見問題</h3>
            <p className="text-sm text-slate-500">有其他問題？歡迎隨時聯繫我們。</p>
          </div>
          <div className="max-w-2xl mx-auto rounded-2xl border border-white/5 bg-slate-900/30 backdrop-blur-sm px-8">
            {faqs.map((item, i) => (
              <FAQItem
                key={i}
                item={item}
                isOpen={openFaq === i}
                onToggle={() => setOpenFaq(openFaq === i ? null : i)}
              />
            ))}
          </div>
        </motion.div>

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