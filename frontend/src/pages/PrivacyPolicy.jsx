import React from 'react';
import { Link } from 'react-router-dom';
import './LegalPage.css';

export default function PrivacyPolicy() {
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
          <h1>隱私權政策 (Privacy Policy)</h1>
          <div className="dv-legal__meta">最後更新日期：2026 年 8 月 27 日</div>
        </header>

        <article className="dv-legal__content">
          <p>
            歡迎使用 <strong>DataVue</strong>（以下簡稱「本服務」或「我們」）。我們非常重視您的個人隱私與數據安全。本隱私權政策旨在向您說明當您訪問本網站（<code>datavue.sitetegy.com</code>）及使用 DataVue 平台服務時，我們如何收集、使用、保護及處理您的個人資訊與第三方授權資料。
          </p>

          <h2>一、我們收集的資訊</h2>
          <p>當您註冊、登入或使用本服務的各項功能時，我們可能收集以下類型的資訊：</p>
          <ul>
            <li><strong>帳號與個人基本資料</strong>：當您透過 Google OAuth 登入時，我們取得您的 Google ID、電子郵件地址（Email）、姓名及公開個人資料圖片，用於建立與識別您的用戶帳號。</li>
            <li><strong>第三方平台授權資料（整合服務）</strong>：
              <ul>
                <li><strong>Google Analytics (GA4)</strong>：若您選擇連線 GA4，我們透過 Google API 讀取您授權之 Google Analytics Property 報表數據（如瀏覽量、事件、轉換率等）。</li>
                <li><strong>Google Search Console (GSC)</strong>：若您選擇連線 GSC，我們透過 Google API 讀取您授權之網站搜尋表現數據（如曝光次數、點擊次數、點閱率、關鍵字排名等）。</li>
                <li><strong>Meta / Facebook Ads</strong>：若您選擇連線 Facebook Ads，我們透過 Meta Marketing API 讀取廣告成效指標（如花費、點擊、ROAS、展示次數等）。</li>
              </ul>
            </li>
            <li><strong>系統操作日誌與 Cookie</strong>：用於保持登入狀態、維持系統安全性與提升使用者體驗。</li>
          </ul>

          <div className="dv-legal__highlight-box">
            <p>
              <strong>🔒 Google API 服務使用者資料政策遵循聲明：</strong><br />
              DataVue 對從 Google API 收到的任何資訊之使用與轉移至其他應用程式，均嚴格遵守 <a href="https://developers.google.com/terms/api-services-user-data-policy" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--legal-cyan)' }}>Google API 服務使用者資料政策</a>（包括<strong>有限使用要求 (Limited Use Requirements)</strong>）。
            </p>
          </div>

          <h2>二、資料的使用目的</h2>
          <p>我們將收集到的數據用於以下特定用途：</p>
          <ul>
            <li><strong>數據視覺化與儀表板展示</strong>：將跨平台（GA4、GSC、Facebook Ads）的指標進行彙整、比較與視覺化圖表呈現。</li>
            <li><strong>AI 智能洞察與診斷</strong>：運用 AI 演算法分析跨渠道成效趨勢，產出策略改善建議。</li>
            <li><strong>自動化報表生成</strong>：依據您的設定產生定期彙總報告與週報。</li>
            <li><strong>用戶身分驗證與帳號安全維護</strong>。</li>
          </ul>

          <h2>三、第三方資料的保護與限制</h2>
          <p>我們對您的第三方數據採取最嚴格的保護措施：</p>
          <ul>
            <li><strong>絕不轉售資料</strong>：我們絕不會將您的個人資料、Google 或 Facebook 授權取得之業務數據出售給任何第三方、廣告商或資料仲介商。</li>
            <li><strong>不用於模型公開訓練</strong>：您的專屬業務數據絕不會被用於公開大型語言模型的基礎訓練。</li>
            <li><strong>最高規格加密</strong>：所有第三方存取憑證（OAuth Access Tokens / Refresh Tokens）皆採用工業級強加密演算法（Fernet / AES）加密儲存於伺服器。</li>
            <li><strong>最小權限原則</strong>：我們僅向第三方 API 申請提供本服務所必需的唯讀（Read-Only）存取權限。</li>
          </ul>

          <h2>四、資料保存與使用者權益（撤銷與刪除）</h2>
          <p>您對自己的個人資料與授權數據擁有完全的控制權：</p>
          <ul>
            <li><strong>中斷整合連線</strong>：您可以隨時在 DataVue 系統設定中中斷與 GA4、GSC 或 Facebook 的連線，系統將立即清除對應的 Access Token。</li>
            <li><strong>透過 Google 撤銷授權</strong>：您可以隨時前往 <a href="https://myaccount.google.com/permissions" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--legal-cyan)' }}>Google 帳戶安全性設定</a> 管理或撤銷 DataVue 對您 Google 帳戶的存取權限。</li>
            <li><strong>請求刪除帳號與資料</strong>：若您希望刪除帳號及系統內的所有關聯資料，請發送郵件至我們的客服信箱，我們將在收到請求後 30 天內完成資料清除。</li>
          </ul>

          <h2>五、政策修訂與更新</h2>
          <p>
            我們可能會不定期修訂本隱私權政策以反映服務變更或法規遵循要求。當有重大變更時，我們將於網站顯著位置發布公告。建議您定期查閱本政策。
          </p>

          <h2>六、聯絡我們</h2>
          <p>
            若您對本隱私權政策或資料處理方式有任何疑問、建議或行使權利之需求，歡迎透過以下方式與我們聯繫：
          </p>
          <ul>
            <li><strong>服務名稱</strong>：DataVue</li>
            <li><strong>官方網域</strong>：<code>datavue.sitetegy.com</code></li>
            <li><strong>客服與隱私支援信箱</strong>：<a href="mailto:info@sitetegy.com" style={{ color: 'var(--legal-cyan)' }}>info@sitetegy.com</a></li>
          </ul>
        </article>

        <footer className="dv-legal__footer">
          &copy; {new Date().getFullYear()} DataVue (<a href="https://sitetegy.com" target="_blank" rel="noopener noreferrer">站略數位科技</a>). All rights reserved.
        </footer>
      </main>
    </div>
  );
}
