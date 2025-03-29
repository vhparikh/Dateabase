import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// User endpoints
export const registerUser = (userData) => {
  return api.post('/users', userData);
};

export const getUser = (userId) => {
  return api.get(`/users/${userId}`);
};

export const updateUser = (userId, userData) => {
  return api.put(`/users/${userId}`, userData);
};

// Experience endpoints
export const createExperience = (experienceData) => {
  return api.post('/experiences', experienceData);
};

export const getExperiences = () => {
  return api.get('/experiences');
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