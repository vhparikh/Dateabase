// API URL configuration
// For production, use a relative URL to ensure it calls the same domain
// For development, use the localhost URL with the correct port
export const API_URL = process.env.NODE_ENV === 'production' 
  ? '/api' // Include /api path for production
  : (process.env.REACT_APP_API_URL || 'http://localhost:5001/api');