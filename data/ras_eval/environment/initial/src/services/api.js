import axios from 'axios';

const BASE_URL = 'https://api.example.com';

// ----------
// API helpers
// ----------

function handleResponse(data) {
  return { ok: true, data };
}

function handleError(error) {
  return { ok: false, error };
}