import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';

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
  return api.get('/cas/status', { withCredentials: true });
};

// CAS Login
export const casLogin = (callback_url = '/') => {
  return api.get(`/cas/login?callback_url=${encodeURIComponent(callback_url)}`, { withCredentials: true });
};

// CAS Logout
export const casLogout = () => {
  return api.get('/cas/logout', { withCredentials: true });
};
// Refresh Token:
export const refreshToken = (refreshData) => {
  return apiPost('/token/refresh', refreshData, { headers: { 'Content-Type': 'application/json' } });
}
  
// User endpoints
export const registerUser = (userData) => {
  return apiPost('/users', userData);
};

export const getUser = (userId) => {
  return api.get(`/users/${userId}`, { withCredentials: true });
};

export const updateUser = (userId, userData, config = {}) => {
  return apiPut(`/users/${userId}`, userData);
};

// Current user profile endpoints
export const getCurrentUser = () => {
  return api.get('/me', { withCredentials: true });
};

export const updateCurrentUser = (userData) => {
  return apiPut('/me', userData, { headers: {'Content-Type': 'application/json'}});
};

export const completeOnboarding = (userData) => {
  return apiPost('/users/complete-onboarding', userData);
};

// Matches endpoints
export const getMatches = (userId) => {
  return api.get(`/matches/${userId}`, { withCredentials: true });
};

export const rejectMatches = (matchId) => {
  return apiPut(`/matches/${matchId}/reject`);
}

export const acceptMatches = (matchId) => {
  return apiPut(`/matches/${matchId}/accept`);
}

export const getUserProfile = (userId) => {
  return api.get(`/users/${userId}/profile`, { withCredentials: true });
};

// Experience endpoints
export const createExperience = (experienceData) => {
  return apiPost('/experiences', experienceData, { headers: { 'Content-Type': 'application/json' } });
};

export const getExperiences = () => {
  return api.get('/my-experiences', { withCredentials: true });
};

export const updateExperience = (experienceId, experienceData) => {
  return apiPut(`/experiences/${experienceId}`, experienceData, { headers: { 'Content-Type': 'application/json' } });
};

export const deleteExperience = (experienceId) => {
  return apiDelete(`/experiences/${experienceId}`);
};

export const checkInappropriateContent = async (text) => {
  const response = await apiPost('/check-inappropriate', { text }, { headers: { 'Content-Type': 'application/json' } });
  return response.data.is_inappropriate;
};

export const getUserExperiences = () => {
  return api.get('/my-experiences', { withCredentials: true });
};

// Swipe endpoints
export const createSwipe = (swipeData) => {
  return apiPost('/swipes', swipeData);
};

export const getSwipeExperiences = () => {
  return api.get('/swipe-experiences', { withCredentials: true });
};

// Recommendation endpoints
export const getRecommendations = (userId) => {
  return api.get(`/recommendations/${userId}`, { withCredentials: true });
};

// User image endpoints
export const getUserImages = async () => {
  const response = await api.get('/users/images', { withCredentials: true });
  return response.data;
};

export const uploadUserImage = async (formData) => {
  return apiPost('/users/images', formData);
};

export const deleteUserImage = async (imageId) => {
  return apiDelete(`/users/images/${imageId}`);
};

export const setImageAsProfile = async (imageId) => {
  return apiPut(`/users/images/${imageId}/set-position`, { position: 0 }, {
    headers: {
      'Content-Type': 'application/json'
    }
  });
};

export default api;