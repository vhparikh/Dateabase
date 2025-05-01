import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json'
  },
  // Always include credentials for session cookies
  withCredentials: true
});

// User endpoints
export const getCSRFToken = () => {
  return api.get('/api/csrf-token')
}
export const registerUser = (userData) => {
  return api.post('/api/users', userData);
};

export const getUser = (userId) => {
  return api.get(`/api/users/${userId}`);
};

export const updateUser = (userId, userData) => {
  return api.put(`/api/users/${userId}`, userData);
};

// Current user profile endpoints
export const getCurrentUser = () => {
  return api.get('/api/me');
};

export const updateCurrentUser = (userData) => {
  return api.put('/api/me', userData);
};

export const completeOnboarding = (userData) => {
  return api.post('/api/users/complete-onboarding', userData);
};

// Experience endpoints
export const createExperience = (experienceData) => {
  return api.post('/api/experiences', experienceData);
};

export const getExperiences = () => {
  return api.get('/api/my-experiences');
};

export const getUserExperiences = () => {
  return api.get('/api/my-experiences');
};

// Swipe endpoints
export const createSwipe = (swipeData) => {
  return api.post('/api/swipes', swipeData);
};

// Match endpoints
export const getMatches = (userId) => {
  return api.get(`/api/matches/${userId}`);
};

// Recommendation endpoints
export const getRecommendations = (userId) => {
  return api.get(`/api/recommendations/${userId}`);
};

export default api; 