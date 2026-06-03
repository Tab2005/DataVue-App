import { motion } from 'framer-motion';
import { ShieldAlert, Sparkles, TrendingUp, Cpu } from 'lucide-react';

const painPoints = [
  {
    num: "01",
    title: "多平台迷航 (Platform Fragmentation)",
    problem: "每天耗費數小時登入 GA4、FB Ads 與 Search Console，在破碎的分頁中試圖手動拼湊真相。",
    solution: "一站式數據熔煉。跨平台指標在同一個空間中被對齊與編排，一眼洞悉大局。",
    accent: "group-hover:border-brand-blue/30"
  },
  {
    num: "02",
    title: "資訊充斥卻缺乏「勝負感」 (Metrics Without Insights)",
    problem: "看著密密麻麻的數字與預算圖表，卻無法回答核心問題：『今天我的下一個動作該是什麼？』",
    solution: "AI 戰略導航。結合多源數據，自動產出明確、可操作且具備商業勝負感的優化決策。",
    accent: "group-hover:border-brand-purple/30"
  },
  {
    num: "03",
    title: "架構僵化與串接斷層 (Brittle Data Structures)",
    problem: "當需要導入新指標或進行特定的內容分組時，受限於傳統報表的死板，難以敏捷調整。",
    solution: "模組化積木架構。高度靈活的數據源配對與自定義指標，隨您的行銷規模共同成長。",
    accent: "group-hover:border-brand-cyan/30"
  }
];

export default function PainPoints() {
  return (
    <section id="solutions" className="py-32 px-6 bg-black/20 border-y border-white/[0.02] relative">
      {/* 裝飾線 */}
      <div className="absolute top-0 left-1/4 w-[1px] h-full bg-gradient-to-b from-white/5 via-transparent to-white/5 hidden lg:block" />

      <div className="max-w-7xl mx-auto relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-16">
          {/* 左側：社論式標題 */}
          <div className="lg:col-span-4 flex flex-col justify-start lg:sticky lg:top-36 h-fit">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-white/5 bg-[#0a0c10]/40 backdrop-blur-md mb-6 w-fit">
              <Cpu className="w-3.5 h-3.5 text-brand-purple" />
              <span className="text-[10px] font-display font-medium tracking-widest text-slate-400 uppercase">THE CRITICAL BLIND SPOTS</span>
            </div>
            
            <h2 className="text-3xl md:text-5xl font-sans font-bold mb-6 text-white leading-tight">
              行銷數據的<br />
              三大<span className="font-serif italic font-normal text-chrome-gradient">致命盲區</span>
            </h2>
            
            <p className="text-slate-500 leading-relaxed text-sm font-light max-w-sm">
              我們懂行銷人與決策者的焦慮。混亂的數據不是資產，而是決策的噪音。
              DataVue 旨在終結這種無序，將冰冷的數字鑄造成進攻市場的利刃。
            </p>
          </div>

          {/* 右側：縱向對稱與不對稱堆疊的「盲區對照卡」 */}
          <div className="lg:col-span-8 flex flex-col gap-8">
            {painPoints.map((item, index) => (
              <motion.div 
                key={index}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-100px" }}
                transition={{ duration: 0.8, delay: index * 0.15, ease: [0.16, 1, 0.3, 1] }}
                className="group relative rounded-3xl border border-white/[0.03] bg-[#07090d]/40 backdrop-blur-md p-8 md:p-10 transition-all duration-500 hover:bg-[#0b0e14]/60 hover:border-white/[0.08]"
              >
                {/* 右上角流光邊角 */}
                <div className={`absolute top-0 right-0 w-24 h-24 bg-gradient-to-tr from-transparent to-white/[0.02] rounded-tr-3xl transition-all duration-500 ${item.accent}`} />

                <div className="flex flex-col md:flex-row gap-8 items-start relative z-10">
                  {/* 序號 - Outfit 超細字體 */}
                  <div className="font-display font-extralight text-5xl md:text-6xl text-slate-700 group-hover:text-slate-500 transition-colors duration-500">
                    {item.num}
                  </div>

                  <div className="flex-1">
                    <h3 className="text-lg md:text-xl font-semibold text-white mb-6 tracking-wide flex items-center gap-2">
                      {item.title}
                    </h3>

                    {/* 痛點與解決方案的極致排版對比 */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 border-t border-white/[0.03]">
                      <div>
                        <div className="text-[10px] font-display font-bold tracking-widest text-slate-500 uppercase mb-2 flex items-center gap-1.5">
                          <ShieldAlert className="w-3 h-3 text-red-500/60" />
                          現狀之痛
                        </div>
                        <p className="text-xs text-slate-500 leading-relaxed group-hover:text-slate-400 transition-colors">
                          {item.problem}
                        </p>
                      </div>

                      <div className="md:border-l md:border-white/[0.03] md:pl-6">
                        <div className="text-[10px] font-display font-bold tracking-widest text-brand-cyan uppercase mb-2 flex items-center gap-1.5">
                          <Sparkles className="w-3 h-3 text-brand-cyan" />
                          DATAVUE 治癒方案
                        </div>
                        <p className="text-xs text-slate-300 leading-relaxed group-hover:text-white transition-colors">
                          {item.solution}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
