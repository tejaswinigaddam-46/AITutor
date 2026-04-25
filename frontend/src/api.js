import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL;
const API_KEY = import.meta.env.VITE_API_KEY;

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'X-API-KEY': API_KEY,
  },
});

export const uploadDocument = async (formData) => {
  const response = await api.post('/documents/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    params: {
      curriculum_book_name: formData.get('curriculum_book_name'),
      document_id: formData.get('document_id'),
      subject: formData.get('subject'),
    },
  });
  return response.data;
};

export const queryRAG = async (queryText) => {
  const response = await api.post('/rag/query', { text: queryText });
  return response.data;
};

export const listDocuments = async () => {
  const response = await api.get('/documents/');
  return response.data;
};

export const checkHealth = async () => {
  const response = await api.get('/health');
  return response.data;
};

export default api;
