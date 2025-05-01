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
  return api.get('/csrf-token')
}
export const registerUser = (userData) => {
  return api.post('/users', userData);
};

export const getUser = (userId) => {
  return api.get(`/users/${userId}`);
};

export const updateUser = (userId, userData) => {
  return api.put(`/users/${userId}`, userData);
};

// Current user profile endpoints
export const getCurrentUser = () => {
  return api.get('/me');
};

export const updateCurrentUser = (userData) => {
  return api.put('/me', userData);
};

export const completeOnboarding = (userData) => {
  return api.post('/users/complete-onboarding', userData);
};

// Experience endpoints
export const createExperience = (experienceData) => {
  return api.post('/experiences', experienceData);
};

export const getExperiences = () => {
  return api.get('/my-experiences');
};

export const getUserExperiences = () => {
  return api.get('/my-experiences');
};

// Swipe endpoints
export const createSwipe = (swipeData) => {
  return api.post('/swipes', swipeData);
};

// Match endpoints
export const getMatches = (userId) => {
  return api.get(`/matches/${userId}`);
};

// Recommendation endpoints
export const getRecommendations = (userId) => {
  return api.get(`/recommendations/${userId}`);
};

export default api; 