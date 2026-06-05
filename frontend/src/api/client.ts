import axios from 'axios'

// Vite proxy가 /cars, /admin, /health를 http://localhost:8000 으로 포워딩
// → baseURL을 ''으로 두면 포트 하드코딩 불필요
const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
  timeout: 30000,
})

export default client
