import React from 'react';
import { Link } from 'react-router-dom';
import './LegalPage.css';

export default function TermsOfService() {
  return (
    <div className="dv-legal">
      <nav className="dv-legal__nav">
        <Link className="dv-legal__brand" to="/">
          <span className="dv-legal__brand-mark">D</span>
          <span>DataVue</span>
        </Link>
        <Link className="dv-legal__back-link" to="/">
          &larr; 返回首頁
        </Link>
      </nav>

      <main className="dv-legal__container">
        <header className="dv-legal__header">
          <h1>服務條款 (Terms of Service)</h1>
          <div className="dv-legal__meta">最後更新日期：2026 年 8 月 27 日</div>
        </header>

        <article className="dv-legal__content">
          <p>
            歡迎使用 <strong>DataVue</strong>（以下簡稱「本服務」或「本平台」）。本服務由 DataVue 團隊（以下簡稱「我們」）維運。在使用本服務前，請詳細閱讀以下服務條款（以下簡稱「本條款」）。當您註冊、登入或使用本服務時，即表示您已閱讀、理解並同意受本條款及我們的《隱私權政策》之約束。
          </p>

          <h2>一、服務內容</h2>
          <p>
            DataVue 是一套行銷數據分析與決策支援平台，主要提供以下服務：
          </p>
          <ul>
            <li>跨平台行銷數據整合（支援 Google Analytics 4、Google Search Console、Facebook Ads 等）。</li>
            <li>行銷成效視覺化儀表板與關鍵績效指標（KPI）追蹤。</li>
            <li>AI 輔助數據洞察、異常診斷與週報生成。</li>
            <li>團隊協作與報表分享功能。</li>
          </ul>

          <h2>二、帳號註冊與安全性</h2>
          <ul>
            <li><strong>身分真實性</strong>：您應使用有效且合法的 Google 帳號進行登入與授權。</li>
            <li><strong>帳號保管責任</strong>：您有責任維持帳號登入資訊之安全性，對於使用您的帳號所進行之所有活動，您需承擔完全之法律責任。</li>
            <li><strong>授權合法性</strong>：當您在 DataVue 中綁定 GA4、GSC 或 Facebook 廣告帳號時，您保證您對該等資產擁有合法的管理或存取權限。</li>
          </ul>

          <h2>三、使用者行為規範</h2>
          <p>您在使用本服務時，同意不得從事下列行為：</p>
          <ul>
            <li>以任何自動化方式（如爬蟲、外掛程式、惡意腳本）未經授權存取或干擾本服務之正常運作。</li>
            <li>嘗試逆向工程、反編譯、破解或規避本系統之任何安全防護機制。</li>
            <li>利用本服務從事任何違反中華民國法令或國際法規之非法活動。</li>
            <li>濫用 API 呼叫導致系統資源過度負載。</li>
          </ul>

          <h2>四、第三方服務與 API 規範</h2>
          <p>
            本服務包含與第三方 API（如 Google API、Meta Marketing API）之整合：
          </p>
          <ul>
            <li>您在使用整合功能時，同時亦受各第三方平台之服務條款約束（包含 <a href="https://developers.google.com/terms" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--legal-cyan)' }}>Google APIs Terms of Service</a>）。</li>
            <li>若第三方平台因政策調整、API 廢除或服務中斷而影響部分功能，我們將盡力維護相容性，但不對第三方服務之可用性承擔保證責任。</li>
          </ul>

          <h2>五、智慧財產權</h2>
          <ul>
            <li><strong>本平台之智慧財產權</strong>：DataVue 平台之所有軟體程式碼、介面設計、商標、圖表與演算法，均屬我們或合法權利人所有，受智慧財產權法規保護。</li>
            <li><strong>您的數據所有權</strong>：您透過本服務整合、匯入與產出之專屬業務數據與報告，所有權仍歸屬於您。</li>
          </ul>

          <h2>六、免責聲明與責任限制</h2>
          <ul>
            <li><strong>服務現狀提供</strong>：本服務係依「現況 (As Is)」及「可用性 (As Available)」基礎提供。我們不保證服務完全不會中斷或毫無錯誤。</li>
            <li><strong>商業決策風險</strong>：DataVue 所提供之 AI 洞察、趨勢分析與報表僅供參考，使用者應自行評估並承擔各項商業與行銷決策之風險。</li>
          </ul>

          <h2>七、條款終止與修改</h2>
          <p>
            我們保留隨時修改本條款之權利。修改後的條款自發布於網站時起生效。若您在條款變更後繼續使用本服務，即視為您已接受修訂後的條款。
          </p>

          <h2>八、聯絡我們</h2>
          <p>
            如果您對本服務條款有任何疑問，請透過以下方式與我們聯繫：
          </p>
          <ul>
            <li><strong>客服信箱</strong>：<a href="mailto:support@sitetegy.com" style={{ color: 'var(--legal-cyan)' }}>support@sitetegy.com</a></li>
            <li><strong>官方網站</strong>：<code>datavue.sitetegy.com</code></li>
          </ul>
        </article>

        <footer className="dv-legal__footer">
          &copy; {new Date().getFullYear()} DataVue (sitetegy.com). All rights reserved.
        </footer>
      </main>
    </div>
  );
}
