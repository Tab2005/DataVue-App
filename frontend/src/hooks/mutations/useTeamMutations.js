/**
 * @fileoverview 團隊相關 Mutation Hooks
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '../../services/apiClient';
import { queryKeys } from '../../constants/queryKeys';

/**
 * 更新團隊設定（支援樂觀更新）
 * @returns {import('@tanstack/react-query').UseMutationResult}
 */
export function useUpdateTeam() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ teamId, data }) =>
      apiClient.put(`/api/teams/${teamId}`, data),

    // 樂觀更新：立即更新 UI，若失敗則回滾
    onMutate: async ({ teamId, data }) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.teams.byId(teamId) });
      const previousTeam = queryClient.getQueryData(queryKeys.teams.byId(teamId));
      queryClient.setQueryData(queryKeys.teams.byId(teamId), (old) => ({
        ...old,
        ...data,
      }));
      return { previousTeam };
    },

    onError: (error, { teamId }, context) => {
      // 回滾至之前的資料
      queryClient.setQueryData(queryKeys.teams.byId(teamId), context.previousTeam);
      console.error('[useUpdateTeam] 更新團隊失敗:', error.message);
    },

    onSuccess: (data, { teamId }) => {
      // 使相關快取失效，觸發重新取得
      queryClient.invalidateQueries({ queryKey: queryKeys.teams.byId(teamId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.teams.mine() });
    },
  });
}

/**
 * 新增團隊成員
 * @returns {import('@tanstack/react-query').UseMutationResult}
 */
export function useCreateInvite() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ teamId }) =>
      apiClient.post(`/api/teams/${teamId}/invites`),

    onSuccess: (data, { teamId }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.teams.invites(teamId) });
    },
  });
}

/**
 * 移除團隊成員
 * @returns {import('@tanstack/react-query').UseMutationResult}
 */
export function useRemoveTeamMember() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ teamId, userId }) =>
      apiClient.delete(`/api/teams/${teamId}/members/${userId}`),

    onSuccess: (data, { teamId }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.teams.members(teamId) });
    },
  });
}

/**
 * 更新團隊成員角色
 * @returns {import('@tanstack/react-query').UseMutationResult}
 */
export function useUpdateMemberRole() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ teamId, userId, role }) =>
      apiClient.put(`/api/teams/${teamId}/members/${userId}`, { role }),

    onSuccess: (data, { teamId }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.teams.members(teamId) });
    },
  });
}
