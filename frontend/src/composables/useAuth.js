import { ref } from 'vue'
import { api } from '../api'

export function useAuth() {
  const token = ref(localStorage.getItem('token') || '')
  const currentUser = ref({
    username: localStorage.getItem('username') || '',
    role: localStorage.getItem('role') || 'user'
  })
  const authTab = ref('login')
  const loginUsername = ref('')
  const loginPassword = ref('')
  const regUsername = ref('')
  const regPassword = ref('')
  const authError = ref('')

  async function doLogin() {
    authError.value = ''
    try {
      const res = await api.login(loginUsername.value, loginPassword.value)
      token.value = res.data.token
      currentUser.value = { username: res.data.username, role: res.data.role }
      localStorage.setItem('token', res.data.token)
      localStorage.setItem('username', res.data.username)
      localStorage.setItem('role', res.data.role)
      return true
    } catch (e) {
      authError.value = e.response?.data?.detail || '登录失败'
      return false
    }
  }

  async function doRegister() {
    authError.value = ''
    try {
      const res = await api.register(regUsername.value, regPassword.value)
      token.value = res.data.token
      currentUser.value = { username: res.data.username, role: res.data.role }
      localStorage.setItem('token', res.data.token)
      localStorage.setItem('username', res.data.username)
      localStorage.setItem('role', res.data.role)
      return true
    } catch (e) {
      authError.value = e.response?.data?.detail || '注册失败'
      return false
    }
  }

  function logout() {
    token.value = ''
    currentUser.value = { username: '', role: 'user' }
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    localStorage.removeItem('role')
  }

  return {
    token,
    currentUser,
    authTab,
    loginUsername,
    loginPassword,
    regUsername,
    regPassword,
    authError,
    doLogin,
    doRegister,
    logout
  }
}
