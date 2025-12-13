export const getAuthToken = () => {
    return localStorage.getItem('google_token');
};

export const getAuthHeaders = () => {
    const token = getAuthToken();
    const teamId = localStorage.getItem('selected_team_id');

    const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
    };

    if (teamId) {
        headers['X-Team-ID'] = teamId;
    }

    return headers;
};

export const clearAuthToken = () => {
    localStorage.removeItem('google_token');
};
