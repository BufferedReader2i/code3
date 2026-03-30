import axios from 'axios'

const API_BASE = 'http://localhost:8000/api'

function authHeaders() {
  const token = localStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export const api = {
  register(username, password) {
    return axios.post(`${API_BASE}/auth/register`, { username, password })
  },

  login(username, password) {
    return axios.post(`${API_BASE}/auth/login`, { username, password })
  },

  changePassword(currentPassword, newPassword) {
    return axios.patch(`${API_BASE}/user/password`, {
      current_password: currentPassword,
      new_password: newPassword
    }, { headers: authHeaders() })
  },

  getInitialRecommendations(userId) {
    return axios.post(`${API_BASE}/recommend`, { user_id: userId })
  },

  classifyText(text) {
    return axios.post(`${API_BASE}/classify`, { text })
  },

  clickNews(userId, newsId) {
    return axios.post(`${API_BASE}/click`, { user_id: userId, news_id: newsId })
  },

  getUserHistory(userId) {
    return axios.get(`${API_BASE}/user/history`, { params: { user_id: userId } })
  },

  getUserHistoryList(userId) {
    return axios.get(`${API_BASE}/user/history/list`, { params: { user_id: userId } })
  },

  getUserProfile(userId) {
    return axios.get(`${API_BASE}/user/profile`, { params: { user_id: userId } })
  },

  deleteUserSubcategory(userId, subcategoryName) {
    return axios.delete(`${API_BASE}/user/profile/subcategory/${encodeURIComponent(subcategoryName)}`, { params: { user_id: userId }, headers: authHeaders() })
  },

  getExampleUsers() {
    return axios.get(`${API_BASE}/users/examples`)
  },

  uploadNews(data) {
    return axios.post(`${API_BASE}/admin/news`, data, { headers: authHeaders() })
  },

  postEvent(payload) {
    return axios.post(`${API_BASE}/event`, payload)
  },

  getUserEvents(userId, limit = 200) {
    return axios.get(`${API_BASE}/user/events`, { params: { user_id: userId, limit } })
  },

  getNewsCategories() {
    return axios.get(`${API_BASE}/news/categories`)
  },

  searchNews({ q = '', category = '', subcategory = '', limit = 50 } = {}) {
    return axios.get(`${API_BASE}/news/search`, { params: { q, category, subcategory, limit } })
  },

  getNewsDetail(newsId, userId = null) {
    const params = userId ? { user_id: userId } : {}
    return axios.get(`${API_BASE}/news/${encodeURIComponent(newsId)}`, { params })
  },

  getSimilarNews(newsId, limit = 12) {
    return axios.get(`${API_BASE}/news/${encodeURIComponent(newsId)}/similar`, { params: { limit } })
  },

  getUserCluster(userId) {
    return axios.get(`${API_BASE}/user/cluster`, { params: { user_id: userId } })
  },

  getUserClusterGraph(userId, limit = 30) {
    return axios.get(`${API_BASE}/user/cluster/graph`, { params: { user_id: userId, limit } })
  },

  adminListNews({ q = '', category = '', status = '', limit = 100 } = {}) {
    return axios.get(`${API_BASE}/admin/news`, { params: { q, category, status, limit }, headers: authHeaders() })
  },

  getFlaggedNews() {
    return axios.get(`${API_BASE}/admin/news/flagged`, { headers: authHeaders() })
  },

  adminUpdateNews(newsId, patch) {
    return axios.patch(`${API_BASE}/admin/news/${encodeURIComponent(newsId)}`, patch, { headers: authHeaders() })
  },

  adminDeleteNews(newsId) {
    return axios.delete(`${API_BASE}/admin/news/${encodeURIComponent(newsId)}`, { headers: authHeaders() })
  },

  adminStatsOverview() {
    return axios.get(`${API_BASE}/admin/stats/overview`, { headers: authHeaders() })
  },

  adminStatsTrends(days = 14) {
    return axios.get(`${API_BASE}/admin/stats/trends`, { params: { days }, headers: authHeaders() })
  },

  adminClusterRebuild({ k = 6, user_limit = 3000 } = {}) {
    return axios.post(`${API_BASE}/admin/cluster/rebuild`, null, { params: { k, user_limit }, headers: authHeaders() })
  }
}

export async function apiCall(url, method = 'GET', data = null) {
 try {
   const config = { headers: authHeaders() }
   let response
   if (method === 'GET') {
     response = await axios.get(url, config)
   } else if (method === 'POST') {
     response = await axios.post(url, data, config)
   } else if (method === 'PATCH') {
     response = await axios.patch(url, data, config)
   } else if (method === 'DELETE') {
     response = await axios.delete(url, config)
   }
   return response.data
 } catch (error) {
   throw new Error(error.response?.data?.message || error.message || '请求失败')
 }
}
