import { motion, AnimatePresence } from 'framer-motion';
import { Search, BarChart3, Bot, Compass, Activity, ArrowUpRight, Zap, Target } from 'lucide-react';
import { FaFacebook } from 'react-icons/fa';
import { useState } from 'react';

const features = [
  {
    id: "gsc",
    icon: <Search className="w-5 h-5 text-blue-400" />,
    title: "GSC 搜尋意圖解碼",
    tabTitle: "Search Console",
    description: "不只是追蹤排名。DataVue 深入剖析關鍵字背後的「真實搜尋意圖」，為您揭示用戶是想尋找知識、進行比較還是準備購買，引導精準的內容策略。",
    metric: "搜尋點擊率提升",
    value: "+18.4%"
  },
  {
    id: "fb",
    icon: <FaFacebook className="w-5 h-5 text-indigo-400" />,
    title: "Facebook Ads 實時追蹤",
    tabTitle: "Facebook Ads",
    description: "打破 Facebook 歸因的黑盒子。實時監控廣告受眾重疊率與真實转化漏斗，防止預算在重疊受眾中相互競價而浪費，將每分錢花在刀口上。",
    metric: "平均轉化成本降低",
    value: "-24.1%"
  },
  {
    id: "ga4",
    icon: <BarChart3 className="w-5 h-5 text-purple-400" />,
    title: "GA4 流量與行為還原",
    tabTitle: "Google Analytics 4",
    description: "將 GA4 複雜的事件還原成直觀的「用戶旅程地圖」。自動進行多維度內容分組，精準找出導致高跳出率的頁面癥結，大幅提升停留時間。",
    metric: "核心頁面停留工時",
    value: "+42.6%"
  },
  {
    id: "ai",
    icon: <Bot className="w-5 h-5 text-emerald-400" />,
    title: "DataVue AI 戰略智庫",
    tabTitle: "AI Studio Core",
    description: "24 小時無休的虛擬數據分析師。整合 Facebook Ads 的消耗、GSC 的趨勢與 GA4 的行為，主動進行數據清洗與關聯性建模，產出可執行的決策報告。",
    metric: "決策響應速度",
    value: "10x Faster"
  }
];

export default function Features() {
  const [activeTab, setActiveTab] = useState("gsc");

  // 取得目前選中的功能
  const currentFeature = features.find(f => f.id === activeTab);

  return (
    <section id="features" className="py-32 px-6 relative overflow-hidden bg-black/10">
      {/* 科技背景裝飾 */}
      <div className="absolute top-1/2 left-0 w-80 h-80 bg-brand-blue/[0.02] rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-0 right-0 w-80 h-80 bg-brand-purple/[0.02] rounded-full blur-[120px] pointer-events-none" />

      <div className="max-w-7xl mx-auto relative z-10">
        {/* 標題 */}
        <div className="text-center mb-20">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-white/5 bg-[#0a0c10]/40 backdrop-blur-md mb-6">
            <Zap className="w-3.5 h-3.5 text-brand-cyan" />
            <span className="text-[10px] font-display font-medium tracking-widest text-slate-400 uppercase">THE CORE ENGINE POWER</span>
          </div>
          
          <h2 className="text-3xl md:text-5xl font-sans font-bold mb-4 text-white">
            解構 DataVue 的<span className="font-serif italic font-normal text-chrome-gradient">數據核心</span>
          </h2>
          <p className="text-slate-500 max-w-xl mx-auto text-sm font-light">
            我們拒絕做簡單的報表搬運工。DataVue 是深度整合多平台數據的超級引擎。
          </p>
        </div>

        {/* 互動式中樞控制台 */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-stretch">
          {/* 左側：控制台切換菜單 */}
          <div className="lg:col-span-5 flex flex-col gap-4 justify-between">
            <div className="flex flex-col gap-3">
              {features.map((feature) => (
                <button
                  key={feature.id}
                  onClick={() => setActiveTab(feature.id)}
                  className={`w-full text-left p-6 rounded-2xl border transition-all duration-300 relative overflow-hidden flex items-center justify-between ${
                    activeTab === feature.id
                      ? "bg-white/[0.03] border-white/10 shadow-[0_10px_30px_rgba(0,0,0,0.4)]"
                      : "bg-transparent border-transparent hover:bg-white/[0.01] hover:border-white/[0.02]"
                  }`}
                >
                  <div className="flex items-center gap-4 relative z-10">
                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center border transition-all duration-300 ${
                      activeTab === feature.id 
                        ? "bg-white text-black border-white" 
                        : "bg-white/5 text-slate-400 border-white/5"
                    }`}>
                      {feature.icon}
                    </div>
                    <div>
                      <h3 className={`font-semibold text-sm transition-colors duration-300 ${
                        activeTab === feature.id ? "text-white" : "text-slate-400"
                      }`}>
                        {feature.title}
                      </h3>
                      <span className="text-[10px] font-display text-slate-500 tracking-wider uppercase">
                        {feature.tabTitle}
                      </span>
                    </div>
                  </div>

                  {activeTab === feature.id && (
                    <motion.div 
                      layoutId="active-indicator"
                      className="absolute left-0 top-0 bottom-0 w-[3px] bg-brand-cyan"
                      transition={{ duration: 0.3 }}
                    />
                  )}

                  <ArrowUpRight className={`w-4 h-4 transition-all duration-300 ${
                    activeTab === feature.id ? "text-white opacity-100 translate-x-0" : "text-slate-600 opacity-0 -translate-x-2"
                  }`} />
                </button>
              ))}
            </div>

            {/* 指標概覽 (與切換選單貼合的精美卡片) */}
            <div className="p-6 rounded-2xl border border-white/[0.03] bg-[#07090d]/30 backdrop-blur-md flex items-center justify-between mt-6">
              <div className="flex items-center gap-3">
                <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-xs text-slate-400 font-light">預估商業增長效率</span>
              </div>
              <div className="text-right">
                <span className="text-2xl font-display font-bold text-white">2.5x</span>
                <span className="text-[10px] text-emerald-400 font-display ml-1.5">Avg. ROI</span>
              </div>
            </div>
          </div>

          {/* 右側：動態運行的模擬控制台畫面 (Interactive Panel) */}
          <div className="lg:col-span-7 rounded-3xl border border-white/[0.03] bg-[#06080c]/50 backdrop-blur-xl p-8 flex flex-col justify-between relative overflow-hidden shadow-[0_30px_60px_rgba(0,0,0,0.8)] min-h-[450px]">
            {/* 炫彩背景流光 */}
            <div className="absolute top-0 right-0 w-64 h-64 bg-brand-blue/5 rounded-full blur-[80px] pointer-events-none" />

            <div className="relative z-10 flex-1 flex flex-col justify-between">
              {/* 控制台頂部欄 */}
              <div className="flex items-center justify-between border-b border-white/[0.05] pb-6 mb-6">
                <div className="flex items-center gap-2">
                  <div className="w-2.5 h-2.5 rounded-full bg-red-500/30" />
                  <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/30" />
                  <div className="w-2.5 h-2.5 rounded-full bg-green-500/30" />
                  <span className="text-[10px] font-display text-slate-500 ml-3">datavue_core_synthesizer.bin</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-brand-cyan animate-ping" />
                  <span className="text-[9px] font-display text-brand-cyan tracking-widest uppercase font-semibold">Active State</span>
                </div>
              </div>

              {/* 內容區域 */}
              <div className="flex-1 flex flex-col justify-center">
                <AnimatePresence mode="wait">
                  <motion.div
                    key={activeTab}
                    initial={{ opacity: 0, y: 15 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -15 }}
                    transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
                    className="flex flex-col gap-6"
                  >
                    <div>
                      <h4 className="text-xl font-bold text-white mb-3">
                        {currentFeature.title}
                      </h4>
                      <p className="text-slate-400 text-xs md:text-sm leading-relaxed font-light">
                        {currentFeature.description}
                      </p>
                    </div>

                    {/* 動態渲染不同的模擬圖表/視覺效果 */}
                    <div className="h-36 rounded-xl border border-white/[0.03] bg-black/40 p-4 relative overflow-hidden flex items-center justify-center">
                      {/* GSC 模擬視覺效果 */}
                      {activeTab === "gsc" && (
                        <div className="w-full h-full flex flex-col justify-between font-display text-[10px]">
                          <div className="flex justify-between items-center text-slate-500 border-b border-white/5 pb-2">
                            <span>INTENT TYPE</span>
                            <span>KEYWORDS BATCH</span>
                            <span>GROWTH RATE</span>
                          </div>
                          <div className="flex-1 flex items-center justify-between mt-2 text-white">
                            <div className="flex flex-col gap-1">
                              <span className="px-2 py-0.5 rounded bg-blue-500/10 border border-blue-500/20 text-blue-400 font-semibold w-fit">TRANSACTIONAL</span>
                              <span className="px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-semibold w-fit">COMMERCIAL</span>
                            </div>
                            <div className="text-slate-400">
                              <div>&gt; 「跨境電商行銷系統比較」</div>
                              <div className="opacity-60">&gt; 「GA4 多源歸因分析指南」</div>
                            </div>
                            <div className="text-right text-emerald-400 font-bold">
                              <div>+342%</div>
                              <div className="opacity-60">+128%</div>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* FB Ads 模擬視覺效果 */}
                      {activeTab === "fb" && (
                        <div className="w-full h-full flex flex-col justify-between">
                          <div className="flex justify-between items-center text-[10px] text-slate-500 border-b border-white/5 pb-2">
                            <span>BUDGET DISTRIBUTION</span>
                            <span>OVERLAP RATE</span>
                          </div>
                          <div className="flex-1 flex items-end gap-2 mt-3 justify-center">
                            <div className="w-16 h-[40%] bg-indigo-500/20 border border-indigo-500/30 rounded-t flex flex-col justify-between p-1.5 text-[8px] font-display text-slate-400">
                              <span>Ad Set A</span>
                              <span className="text-white font-bold">ROAS 1.8</span>
                            </div>
                            <div className="w-16 h-[85%] bg-brand-cyan/20 border border-brand-cyan/30 rounded-t flex flex-col justify-between p-1.5 text-[8px] font-display text-slate-400">
                              <span>Ad Set B</span>
                              <span className="text-white font-bold">ROAS 3.2</span>
                            </div>
                            <div className="w-16 h-[20%] bg-indigo-500/10 border border-indigo-500/20 rounded-t flex flex-col justify-between p-1.5 text-[8px] font-display text-slate-500">
                              <span>Ad Set C</span>
                              <span>Overlap</span>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* GA4 模擬視覺效果 */}
                      {activeTab === "ga4" && (
                        <div className="w-full h-full flex flex-col justify-between font-display text-[10px]">
                          <div className="flex justify-between items-center text-slate-500 border-b border-white/5 pb-2">
                            <span>FUNNEL STAGES</span>
                            <span>DROP-OFF RATE</span>
                          </div>
                          <div className="flex-1 flex flex-col gap-2 justify-center mt-2">
                            <div className="flex items-center gap-2">
                              <span className="w-20 text-slate-400 text-left">1. 著陸頁造訪</span>
                              <div className="flex-1 bg-white/5 h-2 rounded-full overflow-hidden">
                                <div className="bg-brand-purple h-full w-[100%]" />
                              </div>
                              <span className="text-white w-8 text-right">100%</span>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="w-20 text-slate-400 text-left">2. 點擊轉換</span>
                              <div className="flex-1 bg-white/5 h-2 rounded-full overflow-hidden">
                                <div className="bg-brand-cyan h-full w-[42%]" />
                              </div>
                              <span className="text-brand-cyan w-8 text-right">42%</span>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* AI 模擬視覺效果 */}
                      {activeTab === "ai" && (
                        <div className="w-full h-full flex flex-col justify-between font-display text-[9px] text-emerald-400/90 leading-normal">
                          <div className="flex justify-between items-center text-slate-500 border-b border-white/5 pb-2">
                            <span>SYSTEM DEPLOY LOG</span>
                            <span>RESPONSE CODE: 200 OK</span>
                          </div>
                          <div className="flex-1 flex flex-col gap-1 mt-2">
                            <div>[INFO] GA4 content grouping logic compiled. Detected low retention in /checkout.</div>
                            <div>[WARN] FB Ads Set B target overlaps with Set C by 48%. Auto-scaling Set B.</div>
                            <div className="text-white font-bold">[ACTION REQUIRED] Apply Google GSC high-intent keywords to FB Ads creative tags.</div>
                          </div>
                        </div>
                      )}
                    </div>
                  </motion.div>
                </AnimatePresence>
              </div>

              {/* 底部數據標籤 */}
              <div className="border-t border-white/[0.05] pt-6 mt-6 flex justify-between items-center">
                <div>
                  <div className="text-[9px] font-display text-slate-500 uppercase tracking-wider">
                    {currentFeature.metric}
                  </div>
                  <div className="text-lg font-display font-bold text-white">
                    {currentFeature.value}
                  </div>
                </div>
                <div className="flex items-center gap-1.5 px-3 py-1 rounded-full border border-white/5 bg-[#0a0c10]/40 text-[10px] font-display text-slate-400">
                  <Target className="w-3.5 h-3.5 text-brand-cyan" />
                  精準增長指標
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
