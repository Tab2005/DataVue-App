import { useState, useCallback } from 'react';

/**
 * useOptimistic Hook
 * 
 * Provides optimistic update functionality for async operations.
 * Updates UI immediately, then calls API in background.
 * Rolls back if API fails.
 * 
 * Usage:
 * const { execute, isLoading, error } = useOptimistic();
 * 
 * await execute({
 *   optimisticUpdate: () => setItems(items.filter(i => i.id !== id)),
 *   apiCall: () => api.deleteItem(id),
 *   rollback: () => setItems(originalItems),
 *   onSuccess: () => console.log('Deleted!'),
 *   onError: (err) => alert(err.message)
 * });
 */
export function useOptimistic() {
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);

    const execute = useCallback(async ({
        optimisticUpdate,
        apiCall,
        rollback,
        onSuccess,
        onError
    }) => {
        setIsLoading(true);
        setError(null);

        // Step 1: Apply optimistic update immediately
        try {
            if (optimisticUpdate) {
                optimisticUpdate();
            }
        } catch (e) {
            console.error('[Optimistic] Failed to apply optimistic update:', e);
        }

        // Step 2: Call API in background
        try {
            const result = await apiCall();

            // Step 3: Success - keep the optimistic state
            if (onSuccess) {
                onSuccess(result);
            }

            return result;
        } catch (err) {
            // Step 4: Failed - rollback to original state
            console.error('[Optimistic] API call failed, rolling back:', err);
            setError(err);

            if (rollback) {
                try {
                    rollback();
                } catch (e) {
                    console.error('[Optimistic] Failed to rollback:', e);
                }
            }

            if (onError) {
                onError(err);
            }

            throw err;
        } finally {
            setIsLoading(false);
        }
    }, []);

    const clearError = useCallback(() => {
        setError(null);
    }, []);

    return {
        execute,
        isLoading,
        error,
        clearError
    };
}

/**
 * useOptimisticList Hook
 * 
 * Specialized hook for list operations (add, update, remove).
 * Handles common list manipulation patterns.
 * 
 * Usage:
 * const { items, setItems, removeItem, updateItem, addItem } = useOptimisticList(initialItems);
 */
export function useOptimisticList(initialItems = []) {
    const [items, setItems] = useState(initialItems);
    const { execute, isLoading, error, clearError } = useOptimistic();

    const removeItem = useCallback(async (id, apiCall, options = {}) => {
        const originalItems = [...items];
        const itemToRemove = items.find(item => item.id === id);

        return execute({
            optimisticUpdate: () => {
                setItems(items.filter(item => item.id !== id));
            },
            apiCall,
            rollback: () => {
                setItems(originalItems);
            },
            onSuccess: options.onSuccess,
            onError: options.onError || ((err) => {
                console.error('Failed to remove item:', err);
            })
        });
    }, [items, execute]);

    const updateItem = useCallback(async (id, updates, apiCall, options = {}) => {
        const originalItems = [...items];

        return execute({
            optimisticUpdate: () => {
                setItems(items.map(item =>
                    item.id === id ? { ...item, ...updates } : item
                ));
            },
            apiCall,
            rollback: () => {
                setItems(originalItems);
            },
            onSuccess: options.onSuccess,
            onError: options.onError
        });
    }, [items, execute]);

    const addItem = useCallback(async (newItem, apiCall, options = {}) => {
        const originalItems = [...items];
        const tempId = `temp-${Date.now()}`;
        const tempItem = { ...newItem, id: tempId, _isOptimistic: true };

        return execute({
            optimisticUpdate: () => {
                setItems([...items, tempItem]);
            },
            apiCall,
            rollback: () => {
                setItems(originalItems);
            },
            onSuccess: (result) => {
                // Replace temp item with real item from API
                setItems(prev => prev.map(item =>
                    item.id === tempId ? result : item
                ));
                if (options.onSuccess) {
                    options.onSuccess(result);
                }
            },
            onError: options.onError
        });
    }, [items, execute]);

    return {
        items,
        setItems,
        removeItem,
        updateItem,
        addItem,
        isLoading,
        error,
        clearError
    };
}

export default useOptimistic;
