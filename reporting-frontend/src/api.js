// src/api.js
import axios from 'axios';

const API = axios.create({
  baseURL: process.env.REACT_APP_API_BASE_URL,
  // You can add headers here if needed (e.g., auth tokens)
});

export default API;
