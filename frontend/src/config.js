
// For production, use a relative URL to ensure it calls the same domain
// For development, use the localhost URL with the correct port
export const API_URL = process.env.NODE_ENV === 'production' 
  ? '' // Empty string means same domain, which is what we want in production
  : (process.env.REACT_APP_API_URL || 'http://localhost:5001');