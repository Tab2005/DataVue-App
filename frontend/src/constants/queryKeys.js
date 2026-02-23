/**
 * @fileoverview React Query 查詢鍵工廠
 * 統一管理所有 React Query 的 Query Key，確保一致性。
 */

export const queryKeys = {
  // 使用者
  users: {
    all: ['users'],
    me: () => ['users', 'me'],
    byId: (id) => ['users', id],
    list: () => ['users', 'list'],
  },

  // 團隊
  teams: {
    all: ['teams'],
    mine: () => ['teams', 'mine'],
    byId: (id) => ['teams', id],
    members: (teamId) => ['teams', teamId, 'members'],
    invites: (teamId) => ['teams', teamId, 'invites'],
  },

  // Facebook Ads
  facebook: {
    accounts: (userId) => ['facebook', 'accounts', userId],
    insights: (accountId, dateRange) => ['facebook', 'insights', accountId, dateRange],
    campaigns: (accountId) => ['facebook', 'campaigns', accountId],
    trends: (accountId, params) => ['facebook', 'trends', accountId, params],
  },

  // GSC（Google Search Console）
  gsc: {
    data: (params) => ['gsc', 'data', params],
    keywords: (params) => ['gsc', 'keywords', params],
    pages: (params) => ['gsc', 'pages', params],
  },

  // GA4
  ga4: {
    overview: (params) => ['ga4', 'overview', params],
    events: (params) => ['ga4', 'events', params],
    channels: (params) => ['ga4', 'channels', params],
  },

  // 儲存的視圖
  savedViews: {
    all: ['savedViews'],
    byTab: (tab) => ['savedViews', tab],
  },

  // 權限
  permissions: {
    all: ['permissions'],
    mine: () => ['permissions', 'mine'],
  },

  // 管理員
  admin: {
    users: () => ['admin', 'users'],
    teams: () => ['admin', 'teams'],
    stats: () => ['admin', 'stats'],
  },
};
