import axios from 'axios';
import { getCSRFToken, fetchCSRFToken } from './csrf';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add CSRF token to all state-changing requests
api.interceptors.request.use(async (config) => {
  const method = config.method && config.method.toUpperCase();
  if (["POST", "PUT", "PATCH", "DELETE"].includes(method)) {
    // Ensure CSRF token is fetched at least once
    if (!getCSRFToken()) {
      await fetchCSRFToken();
    }
    const token = getCSRFToken();
    if (token) {
      config.headers['X-CSRFToken'] = token;
    }
    config.withCredentials = true;
  }
  return config;
}, (error) => Promise.reject(error));

// Fetch CSRF token at startup
fetchCSRFToken();

// User endpoints
export const registerUser = (userData) => {
  return api.post('/users', userData, { withCredentials: true });
};

export const getUser = (userId) => {
  return api.get(`/users/${userId}`, { withCredentials: true });
};

export const updateUser = (userId, userData) => {
  return api.put(`/users/${userId}`, userData, { withCredentials: true });
};

// Current user profile endpoints
export const getCurrentUser = () => {
  return api.get('/me', { withCredentials: true });
};

export const updateCurrentUser = (userData) => {
  return api.put('/me', userData, { withCredentials: true });
};

export const completeOnboarding = (userData) => {
  return api.post('/users/complete-onboarding', userData, { withCredentials: true });
};

// Experience endpoints
export const createExperience = (experienceData) => {
  return api.post('/experiences', experienceData, { withCredentials: true });
};

export const getExperiences = () => {
  return api.get('/my-experiences', { withCredentials: true });
};

export const getUserExperiences = () => {
  return api.get('/my-experiences', { withCredentials: true });
};

// Swipe endpoints
export const createSwipe = (swipeData) => {
  return api.post('/swipes', swipeData, { withCredentials: true });
};

// Match endpoints
export const getMatches = (userId) => {
  return api.get(`/matches/${userId}`, { withCredentials: true });
};

// Recommendation endpoints
export const getRecommendations = (userId) => {
  return api.get(`/recommendations/${userId}`, { withCredentials: true });
};

export default api; 