import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
})

api.interceptors.response.use(
  (res) => res.data,
  (err) => Promise.reject(err)
)

export default api
