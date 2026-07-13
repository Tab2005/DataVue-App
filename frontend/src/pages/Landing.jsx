import { Link } from 'react-router-dom';
import './Landing.css';

const platformMetrics = [
  { label: 'FB Ads', value: 'ROAS 3.2x', tone: 'blue' },
  { label: 'GSC', value: '+142% 曝光', tone: 'green' },
  { label: 'GA4', value: 'CVR 4.28%', tone: 'amber' },
];

const modules = [
  {
    title: '搜尋意圖解碼',
    label: 'Google Search Console',
    body: '把關鍵字、頁面、國家與裝置拆成可執行的 SEO 優先序。',
  },
  {
    title: '廣告成效校準',
    label: 'Facebook Ads',
    body: '從花費、點擊、ROAS 與素材觀測中找出真正拉動營收的槓桿。',
  },
  {
    title: '流量路徑分析',
    label: 'GA4 Intelligence',
    body: '辨識到達頁、轉換事件與內容分組，讓流量不只停在報表。',
  },
  {
    title: '自動週報輸出',
    label: 'Reporting Engine',
    body: '將跨平台數據整理成可分享的策略報告，減少人工彙整時間。',
  },
];

const pipeline = [
  'Connect',
  'Normalize',
  'Compare',
  'Diagnose',
  'Report',
];

export default function Landing() {
  return (
    <main className="dv-entry">
      <nav className="dv-entry__nav" aria-label="主要導覽">
        <Link className="dv-entry__brand" to="/">
          <span className="dv-entry__brand-mark">D</span>
          <span>DataVue</span>
        </Link>
        <div className="dv-entry__nav-links">
          <a href="#modules">核心模組</a>
          <a href="#workflow">運作流程</a>
          <Link to="/login">登入</Link>
          <Link className="dv-entry__nav-cta" to="/login">免費試用</Link>
        </div>
      </nav>

      <section className="dv-entry__hero">
        <div className="dv-entry__copy">
          <div className="dv-entry__eyebrow">
            <span className="dv-entry__pulse" />
            AI analytics command center
          </div>
          <h1>
            把分散的行銷數據，
            <span>變成可執行的戰略。</span>
          </h1>
          <p className="dv-entry__lead">
            DataVue 將 Facebook Ads、Google Search Console 與 GA4 收斂到同一個決策介面，
            用 AI 協助團隊看懂成效、找出風險，並輸出能直接討論的週報。
          </p>
          <div className="dv-entry__actions">
            <Link className="dv-entry__primary" to="/login">開始連接數據</Link>
            <a className="dv-entry__secondary" href="#modules">查看模組架構</a>
          </div>
          <div className="dv-entry__source-row" aria-label="整合資料來源">
            {platformMetrics.map((item) => (
              <span key={item.label} className={`dv-entry__source dv-entry__source--${item.tone}`}>
                {item.label}
              </span>
            ))}
          </div>
        </div>

        <div className="dv-entry__visual" aria-label="DataVue 系統資料流示意">
          <div className="dv-entry__orbit dv-entry__orbit--outer" />
          <div className="dv-entry__orbit dv-entry__orbit--inner" />
          <div className="dv-entry__core">
            <span>DataVue</span>
            <strong>AI Hub</strong>
          </div>
          {platformMetrics.map((item, index) => (
            <div key={item.label} className={`dv-entry__metric dv-entry__metric--${index + 1}`}>
              <span>{item.label}</span>
              <strong>{item.value}</strong>
            </div>
          ))}
          <div className="dv-entry__insight-card">
            <span>AI 診斷</span>
            <strong>預算偏移偵測</strong>
            <p>高意圖搜尋詞上升，但廣告組尚未同步配置。</p>
          </div>
        </div>
      </section>

      <section id="modules" className="dv-entry__modules" aria-labelledby="modules-title">
        <div className="dv-entry__section-head">
          <span>CORE MODULES</span>
          <h2 id="modules-title">不是更多圖表，而是更短的決策距離。</h2>
        </div>
        <div className="dv-entry__module-grid">
          {modules.map((module) => (
            <article key={module.title} className="dv-entry__module-card">
              <span>{module.label}</span>
              <h3>{module.title}</h3>
              <p>{module.body}</p>
            </article>
          ))}
        </div>
      </section>

      <section id="workflow" className="dv-entry__workflow" aria-labelledby="workflow-title">
        <div>
          <span className="dv-entry__workflow-kicker">OPERATING MODEL</span>
          <h2 id="workflow-title">從串接到週報，一條線完成。</h2>
          <p>
            系統將跨平台資料標準化後，進行趨勢比較、異常診斷與策略摘要。適合代理商、
            成長團隊與需要定期回報的行銷負責人。
          </p>
        </div>
        <ol className="dv-entry__pipeline">
          {pipeline.map((step, index) => (
            <li key={step}>
              <span>{String(index + 1).padStart(2, '0')}</span>
              {step}
            </li>
          ))}
        </ol>
      </section>
    </main>
  );
}
