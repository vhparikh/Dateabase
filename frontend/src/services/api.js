import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Utility to fetch CSRF token
const getCSRFToken = async () => {
  // Remove trailing '/api' if present for correct endpoint
  const base = API_URL.replace(/\/api$/, '');
  const res = await axios.get(`${base}/api/csrf-token`, { withCredentials: true });
  return res.data.csrf_token;
};

// Helper functions for CSRF-protected requests
const apiPost = async (url, data, config = {}) => {
  const csrfToken = await getCSRFToken();
  return api.post(url, data, {
    ...config,
    headers: {
      ...(config.headers || {}),
      'X-CSRFToken': csrfToken
    },
    withCredentials: true
  });
};

const apiPut = async (url, data = {}, config = {}) => {
  const csrfToken = await getCSRFToken();
  return api.put(url, data, {
    ...config,
    headers: {
      ...(config.headers || {}),
      'X-CSRFToken': csrfToken
    },
    withCredentials: true
  });
};

const apiDelete = async (url, config = {}) => {
  const csrfToken = await getCSRFToken();
  return api.delete(url, {
    ...config,
    headers: {
      ...(config.headers || {}),
      'X-CSRFToken': csrfToken
    },
    withCredentials: true
  });
};

// Status:
export const checkStatus = () => {
  return api.get('/api/cas/status', { withCredentials: true });
};

// CAS Login
export const casLogin = (callback_url = '/') => {
  return api.get(`/api/cas/login?callback_url=${encodeURIComponent(callback_url)}`, { withCredentials: true });
};

// CAS Logout
export const casLogout = () => {
  return api.get('/api/cas/logout', { withCredentials: true });
};
// Refresh Token:
export const refreshToken = (refreshData) => {
  return apiPost('/api/token/refresh', refreshData, { headers: { 'Content-Type': 'application/json' } });
}
  
// User endpoints
export const registerUser = (userData) => {
  return apiPost('/api/users', userData);
};

export const getUser = (userId) => {
  return api.get(`/api/users/${userId}`, { withCredentials: true });
};

export const updateUser = (userId, userData, config = {}) => {
  return apiPut(`/api/users/${userId}`, userData);
};

// Current user profile endpoints
export const getCurrentUser = () => {
  return api.get('/api/me', { withCredentials: true });
};

export const updateCurrentUser = (userData) => {
  return apiPut('/api/me', userData, { headers: {'Content-Type': 'application/json'}});
};

export const completeOnboarding = (userData) => {
  return apiPost('/api/users/complete-onboarding', userData);
};

// Matches endpoints
export const getMatches = (userId) => {
  return api.get(`/api/matches/${userId}`, { withCredentials: true });
};

export const rejectMatches = (matchId) => {
  return apiPut(`/api/matches/${matchId}/reject`);
}

export const acceptMatches = (matchId) => {
  return apiPut(`/api/matches/${matchId}/accept`);
}

export const getUserProfile = (userId) => {
  return api.get(`/api/users/${userId}/profile`, { withCredentials: true });
};

// Experience endpoints
export const createExperience = (experienceData) => {
  return apiPost('/api/experiences', experienceData, { headers: { 'Content-Type': 'application/json' } });
};

export const getExperiences = () => {
  return api.get('/api/my-experiences', { withCredentials: true });
};

export const updateExperience = (experienceId, experienceData) => {
  return apiPut(`/api/experiences/${experienceId}`, experienceData, { headers: { 'Content-Type': 'application/json' } });
};

export const deleteExperience = (experienceId) => {
  return apiDelete(`/api/experiences/${experienceId}`);
};

export const checkInappropriateContent = async (text) => {
  const response = await apiPost('/api/check-inappropriate', { text }, { headers: { 'Content-Type': 'application/json' } });
  return response.data.is_inappropriate;
};

export const getUserExperiences = () => {
  return api.get('/api/my-experiences', { withCredentials: true });
};

// Swipe endpoints
export const createSwipe = (swipeData) => {
  return apiPost('/api/swipes', swipeData);
};

export const getSwipeExperiences = async () => {
  const response = await fetch('/api/swipe-experiences', {
    method: 'GET',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json'
    }
  });
  return response;
};

// Recommendation endpoints
export const getRecommendations = (userId) => {
  return api.get(`/api/recommendations/${userId}`, { withCredentials: true });
};

// User image endpoints
export const getUserImages = async () => {
  const response = await api.get('/api/users/images', { withCredentials: true });
  return response.data;
};

export const uploadUserImage = async (formData) => {
  return apiPost('/api/users/images', formData);
};

export const deleteUserImage = async (imageId) => {
  return apiDelete(`/api/users/images/${imageId}`);
};

export const setImageAsProfile = async (imageId) => {
  return apiPut(`/api/users/images/${imageId}/set-position`, { position: 0 }, {
    headers: {
      'Content-Type': 'application/json'
    }
  });
};

export default api;