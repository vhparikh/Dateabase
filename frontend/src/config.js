// API URL configuration
// Use relative URLs in production and full URLs in development
const isProduction = process.env.NODE_ENV === 'production';
export const API_URL = process.env.REACT_APP_API_URL || (isProduction ? '' : 'http://localhost:5001'); 