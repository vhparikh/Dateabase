// For production deployments, use relative URLs
// Empty string means requests will be sent to the same domain as where the app is hosted
// This ensures requests work on Heroku or other platforms automatically
export const API_URL = process.env.NODE_ENV === 'production' 
  ? '' // Using empty string forces same-origin requests for wherever the app is deployed
  : (process.env.REACT_APP_API_URL || 'http://localhost:5001');