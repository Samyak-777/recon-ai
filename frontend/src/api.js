/**
 * ReconAI API Client Configuration
 * Automatically routes to Render backend in production or Vite proxy in development.
 */
const API_BASE = import.meta.env.VITE_API_URL || '';

export const apiUrl = (endpoint) => {
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  return `${API_BASE}${cleanEndpoint}`;
};

export default apiUrl;
