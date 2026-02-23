/**
 * @fileoverview 我的團隊列表 Query Hook
 */

import { useQuery } from '@tanstack/react-query';
import apiClient from '../../services/apiClient';
import { queryKeys } from '../../constants/queryKeys';

/**
 * 取得當前使用者所屬的所有團隊
 * @returns {import('@tanstack/react-query').UseQueryResult<import('../../types/api').Team[]>}
 */
export function useMyTeams() {
  return useQuery({
    queryKey: queryKeys.teams.mine(),
    queryFn: () => apiClient.get('/api/teams/me'),
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * 取得特定團隊資料
 * @param {string} teamId - 團隊 ID
 * @returns {import('@tanstack/react-query').UseQueryResult<import('../../types/api').Team>}
 */
export function useTeam(teamId) {
  return useQuery({
    queryKey: queryKeys.teams.byId(teamId),
    queryFn: () => apiClient.get(`/api/teams/${teamId}`),
    staleTime: 5 * 60 * 1000,
    enabled: Boolean(teamId),
  });
}

/**
 * 取得團隊成員列表
 * @param {string} teamId - 團隊 ID
 * @returns {import('@tanstack/react-query').UseQueryResult<import('../../types/api').TeamMember[]>}
 */
export function useTeamMembers(teamId) {
  return useQuery({
    queryKey: queryKeys.teams.members(teamId),
    queryFn: () => apiClient.get(`/api/teams/${teamId}/members`),
    staleTime: 5 * 60 * 1000,
    enabled: Boolean(teamId),
  });
}
