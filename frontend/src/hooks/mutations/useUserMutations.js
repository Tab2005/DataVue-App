/**
 * @fileoverview 使用者相關 Mutation Hooks
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '../../services/apiClient';
import { queryKeys } from '../../constants/queryKeys';

/**
 * 管理員更新使用者（角色/狀態）
 * @returns {import('@tanstack/react-query').UseMutationResult}
 */
export function useUpdateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ userId, data }) =>
      apiClient.put(`/users/${userId}`, data),

    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.users.list() });
      queryClient.invalidateQueries({ queryKey: queryKeys.admin.users() });
    },
  });
}

/**
 * 管理員刪除使用者
 * @returns {import('@tanstack/react-query').UseMutationResult}
 */
export function useDeleteUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ userId }) =>
      apiClient.delete(`/users/${userId}`),

    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.users.list() });
      queryClient.invalidateQueries({ queryKey: queryKeys.admin.users() });
    },
  });
}
