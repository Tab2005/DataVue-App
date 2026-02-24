/**
 * @fileoverview 管理後台 Query Hooks
 */

import { useQuery } from '@tanstack/react-query';
import apiClient from '../../services/apiClient';
import { queryKeys } from '../../constants/queryKeys';

/**
 * 取得所有使用者（管理員限定）
 * @returns {import('@tanstack/react-query').UseQueryResult}
 */
export function useAdminUsers() {
  return useQuery({
    queryKey: queryKeys.admin.users(),
    queryFn: () => apiClient.get('/api/admin/users'),
    staleTime: 2 * 60 * 1000,
  });
}

/**
 * 取得所有團隊（管理員限定）
 * @returns {import('@tanstack/react-query').UseQueryResult}
 */
export function useAdminTeams() {
  return useQuery({
    queryKey: queryKeys.admin.teams(),
    queryFn: () => apiClient.get('/api/admin/teams'),
    staleTime: 2 * 60 * 1000,
  });
}

/**
 * 取得系統統計（管理員限定）
 * @returns {import('@tanstack/react-query').UseQueryResult}
 */
export function useAdminStats() {
  return useQuery({
    queryKey: queryKeys.admin.stats(),
    queryFn: () => apiClient.get('/api/admin/stats'),
    staleTime: 1 * 60 * 1000,
  });
}
