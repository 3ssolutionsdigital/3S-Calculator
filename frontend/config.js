// Use the local API while developing on this machine, and Render when deployed.
const isLocalFrontend = ['localhost', '127.0.0.1'].includes(window.location.hostname);
window.API_BASE = isLocalFrontend
  ? 'http://127.0.0.1:8000/api/v1'
  : 'https://threes-calculator.onrender.com/api/v1';
