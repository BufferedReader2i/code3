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

  getLLMProfile(userId) {
    return axios.get(`${API_BASE}/user/profile/llm`, { params: { user_id: userId }, headers: authHeaders() })
  },

  getRecommendationsWithReasons(userId) {
    return axios.post(`${API_BASE}/recommend`, { user_id: userId, with_reasons: true })
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
  },

  // ======== LLM对话式推荐API（新增） ========
  getLLMStatus() {
    return axios.get(`${API_BASE}/llm/status`)
  },

  llmChat(message, userId, history = []) {
    return axios.post(`${API_BASE}/llm/chat`, {
      message: message,
      user_id: userId,
      history: history || []
    }, { headers: authHeaders() })
  },

  clearLLMHistory() {
    return axios.post(`${API_BASE}/llm/chat/clear`, {}, { headers: authHeaders() })
  },

  // 流式对话API - 使用SSE (Server-Sent Events)
  llmChatStream(message, userId, onToken, onRecommendations, onDone, onError) {
    const token = localStorage.getItem('token')
    const url = `${API_BASE}/llm/chat/stream`
    
    // 使用fetch API支持流式读取
    fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : ''
      },
      body: JSON.stringify({
        message: message,
        user_id: userId
      })
    })
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      
      function read() {
        reader.read().then(({ done, value }) => {
          if (done) {
            if (buffer.trim()) {
              // 处理剩余数据
              processLine(buffer)
            }
            if (onDone) onDone()
            return
          }
          
          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() || '' // 保留未完成的行
          
          for (const line of lines) {
            processLine(line)
          }
          
          read()
        }).catch(err => {
          if (onError) onError(err.message)
        })
      }
      
      function processLine(line) {
        if (!line.trim()) return
        
        // SSE格式: data: {...}
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            if (data.type === 'token' && onToken) {
              onToken(data.content)
            } else if (data.type === 'recommendations' && onRecommendations) {
              onRecommendations(data.content)
            } else if (data.type === 'done') {
              // 完成信号在reader结束时处理
            } else if (data.type === 'error' && onError) {
              onError(data.content)
            }
          } catch (e) {
            console.error('Parse SSE error:', e)
          }
        }
      }
      
      read()
    })
    .catch(err => {
      if (onError) onError(err.message)
    })
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
