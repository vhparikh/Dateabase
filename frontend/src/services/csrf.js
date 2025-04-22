// csrf.js
// Utility to fetch and store CSRF token, and helper to get it from cookie
import axios from 'axios';

// Fetch CSRF token from backend and store in cookie
export async function fetchCSRFToken() {
  try {
    await axios.get('/api/csrf-token', { withCredentials: true });
    // Token is now set in the cookie by backend
  } catch (err) {
    console.error('Failed to fetch CSRF token:', err);
  }
}

// Get CSRF token from cookie
export function getCSRFToken() {
  const match = document.cookie.match(new RegExp('(^| )csrf_token=([^;]+)'));
  if (match) return match[2];
  return null;
}
