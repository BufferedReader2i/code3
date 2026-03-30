<template>
  <div id="app">
    <AppHeader
      :current-page="currentPage"
      :token="token"
      :current-user="currentUser"
      @navigate="onNavigate"
      @logout="handleLogout"
    />

    <main v-if="!token" class="login-page">
      <div class="login-card">
        <h2>登录 / 注册</h2>
        <div class="login-tabs">
          <button type="button" class="login-tab" :class="{ active: authTab === 'login' }" @click="authTab = 'login'">登录</button>
          <button type="button" class="login-tab" :class="{ active: authTab === 'register' }" @click="authTab = 'register'">注册</button>
        </div>
        <div v-if="authTab === 'login'" class="login-form">
          <input v-model="loginUsername" type="text" placeholder="用户名">
          <input v-model="loginPassword" type="password" placeholder="密码">
          <button type="button" class="btn-primary" @click="handleLogin">登录</button>
          <p v-if="authError" class="auth-err">{{ authError }}</p>
        </div>
        <div v-else class="login-form">
          <input v-model="regUsername" type="text" placeholder="用户名">
          <input v-model="regPassword" type="password" placeholder="密码">
          <button type="button" class="btn-primary" @click="handleRegister">注册</button>
          <p v-if="authError" class="auth-err">{{ authError }}</p>
        </div>
      </div>
    </main>

    <template v-else-if="token">
      <RecommendView
        v-if="currentPage === 'recommend'"
        :recommendations="recommendations"
        :loading="loading"
        :error="error"
        @refresh="loadInitialRecommendations"
        @open-detail="openNewsDetail"
        @like="onLike"
        @unlike="onUnlike"
        @dislike="onDislike"
        @undislike="onUndislike"
        @favorite="onFavorite"
        @unfavorite="onUnfavorite"
        @not-interested="onNotInterested"
        @remove-not-interested="onRemoveNotInterested"
      />
      <NewsDetailView
        v-else-if="currentPage === 'detail' && selectedNews"
        :news="selectedNews"
        :user-id="currentUser.username"
        @back="backFromDetail"
        @like="onDetailLike"
        @unlike="onDetailUnlike"
      />
      <SearchView
        v-else-if="currentPage === 'search'"
        v-model:q="searchQ"
        v-model:category="searchCategory"
        v-model:subcategory="searchSubcategory"
        :items="searchItems"
        :loading="searchLoading"
        :error="searchError"
        @search="doSearch"
        @open="openNewsDetail"
      />
      <ProfileView
        v-else-if="currentPage === 'profile'"
        :user-id="currentUser.username"
        :user-profile="userProfile"
        :profile-loading="profileLoading"
        :pie-categories-legend="pieCategoriesLegend"
        :user-cluster="userCluster"
      />
      <HistoryView
        v-else-if="currentPage === 'history'"
        :history-list="historyList"
        :history-loading="historyLoading"
        :history-count="historyCount"
        @open-detail="openNewsDetail"
      />
      <FavoritesView
        v-else-if="currentPage === 'favorites'"
        :user-id="currentUser.username"
        @open-detail="openNewsDetail"
      />
      <UploadView
        ref="uploadViewRef"
        v-else-if="currentPage === 'upload' && isAdmin"
        v-model:upload-title="uploadTitle"
        v-model:upload-abstract="uploadAbstract"
        v-model:upload-body="uploadBody"
        v-model:upload-category="uploadCategory"
        v-model:upload-subcategory="uploadSubcategory"
        :upload-result="uploadResult"
        :upload-error="currentPage === 'upload' ? error : ''"
        :batch-news-list="batchNewsList"
        :selected-news-index="selectedNewsIndex"
        @auto-recognize="autoRecognize"
        @submit="submitUpload"
        @batch-upload="handleBatchUpload"
        @select-news="selectNews"
      />
      <NewsManagementView
        v-else-if="currentPage === 'news-management' && isAdmin"
      />
      <AdminView
        v-else-if="currentPage === 'admin' && isAdmin"
        :overview="adminOverview"
        :cluster-users="adminClusterUsers"
        :cluster-k="adminClusterK"
        :error="adminError"
        @refresh="refreshAdmin"
        @rebuild-clusters="rebuildClusters"
      />
      <div v-if="feedbackToast" class="feedback-toast">{{ feedbackToast }}</div>
    </template>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { api } from './api.js'
import { useAuth } from './composables/useAuth'
import { buildPie } from './utils/pieChart'
import AppHeader from './components/AppHeader.vue'
import RecommendView from './components/RecommendView.vue'
import NewsDetailView from './components/NewsDetailView.vue'
import ProfileView from './components/ProfileView.vue'
import HistoryView from './components/HistoryView.vue'
import UploadView from './components/UploadView.vue'
import SearchView from './components/SearchView.vue'
import AdminView from './components/AdminView.vue'
import NewsManagementView from './components/NewsManagementView.vue'
import FavoritesView from './components/FavoritesView.vue'

export default {
  name: 'App',
  components: {
    AppHeader,
    RecommendView,
    NewsDetailView,
    ProfileView,
    HistoryView,
    UploadView,
    SearchView,
    AdminView,
    NewsManagementView,
    FavoritesView
  },
  setup() {
    // 异步任务队列
    const asyncTaskQueue = ref([])
    const isProcessingQueue = ref(false)
    
    // 处理异步任务队列
    async function processQueue() {
      if (isProcessingQueue.value || asyncTaskQueue.value.length === 0) return
      
      isProcessingQueue.value = true
      
      while (asyncTaskQueue.value.length > 0) {
        const task = asyncTaskQueue.value.shift()
        try {
          await task()
        } catch (error) {
          console.warn('异步任务执行失败:', error)
          // 可选：重试机制可以在这里实现
        }
      }
      
      isProcessingQueue.value = false
    }
    
    // 添加任务到队列
    function addAsyncTask(task) {
      asyncTaskQueue.value.push(task)
      if (!isProcessingQueue.value) {
        setTimeout(processQueue, 0)
      }
    }
    
    const auth = useAuth()
    const {
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
    } = auth

    const uploadViewRef = ref(null)
    const currentPage = ref('recommend')
    const selectedNews = ref(null)
    const detailEnterAt = ref(0)
    const recommendations = ref([])
    const loading = ref(false)
    const error = ref('')
    const userProfile = ref(null)
    const profileLoading = ref(false)
    const userCluster = ref(null)
    const historyList = ref([])
    const historyLoading = ref(false)
    const historyCount = ref(null)

    const searchQ = ref('')
    const searchCategory = ref('')
    const searchSubcategory = ref('')
    const searchItems = ref([])
    const searchLoading = ref(false)
    const searchError = ref('')

    const adminOverview = ref(null)
    const adminClusterUsers = ref(0)
    const adminClusterK = ref(0)
    const adminError = ref('')

    const uploadTitle = ref('')
    const uploadAbstract = ref('')
    const uploadBody = ref('')
    const uploadCategory = ref('')
    const uploadSubcategory = ref('')
    const uploadResult = ref('')
    const batchNewsList = ref([])
    const selectedNewsIndex = ref(-1)

    const isAdmin = computed(() => currentUser.value.role === 'admin')

    const pieCategoriesLegend = computed(() => {
      if (!userProfile.value?.categories?.length) return []
      return buildPie(userProfile.value.categories).legend
    })

    async function handleLogin() {
      const ok = await doLogin()
      if (ok) currentPage.value = 'recommend'
    }

    async function handleRegister() {
      const ok = await doRegister()
      if (ok) currentPage.value = 'recommend'
    }

    function handleLogout() {
      logout()
      recommendations.value = []
      userProfile.value = null
      historyList.value = []
      selectedNews.value = null
      currentPage.value = 'recommend'
    }

    function onNavigate(page) {
      if (page === 'profile') goProfile()
      else if (page === 'history') goHistory()
      else if (page === 'admin') goAdmin()
      else if (page === 'favorites') currentPage.value = 'favorites'
      else currentPage.value = page
    }

    async function fetchUserProfile(uid) {
      if (!uid) {
        userProfile.value = null
        return
      }
      profileLoading.value = true
      try {
        const res = await api.getUserProfile(uid)
        userProfile.value = res.data
      } catch (_) {
        userProfile.value = null
      } finally {
        profileLoading.value = false
      }
    }

    function goProfile() {
      currentPage.value = 'profile'
      const uid = currentUser.value.username
      if (uid) {
        fetchUserProfile(uid)
        api.getUserCluster(uid).then(res => { userCluster.value = res.data }).catch(() => { userCluster.value = null })
      }
    }

    async function doSearch() {
      searchLoading.value = true
      searchError.value = ''
      try {
        const res = await api.searchNews({
          q: searchQ.value,
          category: searchCategory.value,
          subcategory: searchQ.value,
          limit: 50
        })
        const items = res.data?.items || []
        // normalize to NewsCard shape
        searchItems.value = items.map(x => ({
          id: x.news_id,
          title: x.title,
          abstract: x.abstract,
          category: x.category,
          subcategory: x.subcategory
        }))
      } catch (e) {
        searchItems.value = []
        searchError.value = '搜索失败: ' + (e.message || '网络错误')
      } finally {
        searchLoading.value = false
      }
    }

    const feedbackToast = ref('')
    let feedbackToastTimer = null
    function showFeedbackToast(msg) {
      feedbackToast.value = msg
      if (feedbackToastTimer) clearTimeout(feedbackToastTimer)
      feedbackToastTimer = setTimeout(() => { feedbackToast.value = '' }, 1500)
    }

    async function postSimpleEvent(type, news) {
      const uid = currentUser.value.username
      if (!uid || !news?.id) return true
      try {
        const res = await api.postEvent({ user_id: uid, news_id: news.id, event_type: type })
        return res.data?.saved !== false
      } catch (_) {
        return false
      }
    }

    async function onLike(news) {
      const saved = await postSimpleEvent('like', news)
      showFeedbackToast(saved ? '已赞' : '反馈未保存（请检查数据库或网络）')
    }
    async function onUnlike(news) {
      const saved = await postSimpleEvent('unlike', news)
      showFeedbackToast(saved ? '已取消赞' : '反馈未保存（请检查数据库或网络）')
    }
    async function onDislike(news) {
      const saved = await postSimpleEvent('dislike', news)
      showFeedbackToast(saved ? '已踩' : '反馈未保存（请检查数据库或网络）')
    }
    async function onUndislike(news) {
      const saved = await postSimpleEvent('undislike', news)
      showFeedbackToast(saved ? '已取消踩' : '反馈未保存（请检查数据库或网络）')
    }
    async function onFavorite(news) {
      const saved = await postSimpleEvent('favorite', news)
      showFeedbackToast(saved ? '已收藏' : '反馈未保存（请检查数据库或网络）')
    }
    async function onUnfavorite(news) {
      const saved = await postSimpleEvent('unfavorite', news)
      showFeedbackToast(saved ? '已取消收藏' : '反馈未保存（请检查数据库或网络）')
    }
    async function onNotInterested(news) {
      const saved = await postSimpleEvent('not_interested', news)
      showFeedbackToast(saved ? '已标记不感兴趣' : '反馈未保存（请检查数据库或网络）')
    }
    async function onRemoveNotInterested(news) {
      const saved = await postSimpleEvent('remove_not_interested', news)
      showFeedbackToast(saved ? '已取消不感兴趣' : '反馈未保存（请检查数据库或网络）')
    }

    function goHistory() {
      currentPage.value = 'history'
      const uid = currentUser.value.username
      historyLoading.value = true
      error.value = ''
      historyCount.value = null
      if (uid) {
        api.getUserProfile(uid)
          .then(res => { historyCount.value = res.data?.history_count ?? 0 })
          .catch(() => { historyCount.value = 0 })
        api.getUserHistoryList(uid)
          .then(res => { historyList.value = res.data?.items || [] })
          .catch(() => { historyList.value = [] })
          .finally(() => { historyLoading.value = false })
      } else {
        historyList.value = []
        historyCount.value = 0
        historyLoading.value = false
      }
    }

    async function loadInitialRecommendations() {
      const uid = currentUser.value.username
      if (!uid) {
        error.value = '请先登录'
        return
      }
      loading.value = true
      error.value = ''
      recommendations.value = [] // 先清空，让界面立即进入加载状态
      try {
        await fetchUserProfile(uid)
        const res = await api.getInitialRecommendations(uid)
        const list = res.data?.recommendations
        recommendations.value = Array.isArray(list) ? [...list] : []
      } catch (e) {
        error.value = '获取推荐失败: ' + (e.message || '网络错误')
      } finally {
        loading.value = false
      }
    }

    /** 点击新闻：立即进入详情页，后台异步处理点击事件、用户画像更新和推荐计算 */
    async function openNewsDetail(news) {
      const uid = currentUser.value.username
      if (!uid) {
        error.value = '请先登录'
        return
      }
      
      // 1. 立即进入详情页（不等待任何API调用）
      error.value = ''
      detailEnterAt.value = Date.now()
      selectedNews.value = news // 先使用原始数据
      currentPage.value = 'detail'
      
      // 2. 异步获取新闻详情（用户需要看到完整信息）
      try {
        const res = await api.getNewsDetail(news.id, uid)
        const detail = res.data
        selectedNews.value = {
          ...news,
          subcategory: detail.subcategory || news.subcategory || '',
          like_count: detail.like_count || 0,
          user_liked: detail.user_liked || false
        }
      } catch (_) {
        // 如果获取详情失败，继续使用原始数据
        selectedNews.value = news
      }
      
      // 3. 后台异步处理点击事件和用户画像更新（不阻塞UI）
      setTimeout(async () => {
        try {
          // 3.1 记录点击事件（不等待响应）
          api.clickNews(uid, news.id).catch(() => {
            console.warn('点击事件上报失败，但不影响用户体验')
          })
          
          // 3.2 异步更新用户画像
          fetchUserProfile(uid).catch(() => {
            console.warn('用户画像更新失败')
          })
          
          // 3.3 后台刷新推荐列表（为返回时做准备）
          loadInitialRecommendations().catch(() => {
            console.warn('推荐列表刷新失败')
          })
          
        } catch (error) {
          console.error('后台异步处理异常:', error)
        }
      }, 0) // 使用setTimeout确保异步执行
    }

    async function backFromDetail() {
      const uid = currentUser.value.username
      const nid = selectedNews.value?.id
      const enterAt = detailEnterAt.value
      currentPage.value = 'recommend'
      if (uid && nid && enterAt) {
        const dwell = Math.max(0, Date.now() - enterAt)
        detailEnterAt.value = 0
        try {
          await api.postEvent({ user_id: uid, news_id: nid, event_type: 'dwell', dwell_ms: dwell })
        } catch (_) {}
      }
    }

    function onDetailLike(newsId) {
      // 点赞成功后刷新用户画像
      fetchUserProfile(currentUser.value.username)
    }

    function onDetailUnlike(newsId) {
      // 取消点赞后刷新用户画像
      fetchUserProfile(currentUser.value.username)
    }

    async function refreshAdmin() {
      adminError.value = ''
      try {
        const [ov] = await Promise.all([api.adminStatsOverview()])
        adminOverview.value = ov.data
      } catch (e) {
        adminOverview.value = null
        adminError.value = e.response?.data?.detail || ('加载统计失败: ' + (e.message || '网络错误'))
      }
    }

    async function rebuildClusters() {
      adminError.value = ''
      try {
        const res = await api.adminClusterRebuild({ k: 6, user_limit: 3000 })
        adminClusterUsers.value = res.data?.users ?? 0
        adminClusterK.value = res.data?.clusters ?? 0
      } catch (e) {
        adminError.value = e.response?.data?.detail || ('重算失败: ' + (e.message || '网络错误'))
      }
    }

    function goAdmin() {
      currentPage.value = 'admin'
      refreshAdmin().catch(() => {})
    }

    async function autoRecognize() {
      const text = (uploadTitle.value + ' ' + uploadAbstract.value).trim()
      if (!text) {
        error.value = '请先填写标题或摘要'
        return
      }
      error.value = ''
      try {
        const res = await api.classifyText(text)
        uploadCategory.value = res.data.category || ''
        uploadResult.value = `已识别为：${res.data.category}，置信度 ${(res.data.confidence * 100).toFixed(1)}%`
      } catch (e) {
        error.value = '识别失败: ' + (e.message || '网络错误')
      }
    }

    async function submitUpload() {
      if (!uploadTitle.value.trim()) {
        error.value = '请填写标题'
        return
      }
      error.value = ''
      uploadResult.value = ''
      try {
        const res = await api.uploadNews({
          title: uploadTitle.value,
          abstract: uploadAbstract.value,
          body: uploadBody.value,
          category: uploadCategory.value || 'N/A',
          subcategory: uploadSubcategory.value || 'N/A'
        })
        // 上传成功后从列表中移除该新闻
        if (selectedNewsIndex.value >= 0 && batchNewsList.value.length > 0) {
          batchNewsList.value.splice(selectedNewsIndex.value, 1)
          selectedNewsIndex.value = -1
        }
        // 清空表单
        uploadTitle.value = ''
        uploadAbstract.value = ''
        uploadBody.value = ''
        uploadCategory.value = ''
        uploadSubcategory.value = ''
        uploadResult.value = `上传成功，新闻 ID：${res.data.news_id}`
      } catch (e) {
        error.value = e.response?.data?.detail || '上传失败: ' + (e.message || '网络错误')
      }
    }

    function handleBatchUpload(payload) {
      if (payload.error) {
        error.value = payload.error
        batchNewsList.value = []
        selectedNewsIndex.value = -1
        return
      }
      const rows = payload.rows
      if (!rows || rows.length === 0) {
        error.value = 'CSV 文件为空'
        batchNewsList.value = []
        selectedNewsIndex.value = -1
        return
      }
      // 存储整个新闻列表
      batchNewsList.value = rows
      // 默认选择第一行
      selectedNewsIndex.value = 0
      const firstRow = rows[0]
      uploadTitle.value = firstRow.title || ''
      uploadAbstract.value = firstRow.abstract || ''
      uploadBody.value = firstRow.body || ''
      uploadCategory.value = firstRow.category || ''
      uploadSubcategory.value = firstRow.subcategory || ''
      error.value = ''
      showFeedbackToast(`已加载 ${rows.length} 条新闻`)
    }

    function selectNews(index) {
      if (index < 0 || index >= batchNewsList.value.length) return
      selectedNewsIndex.value = index
      const news = batchNewsList.value[index]
      uploadTitle.value = news.title || ''
      uploadAbstract.value = news.abstract || ''
      uploadBody.value = news.body || ''
      uploadCategory.value = news.category || ''
      uploadSubcategory.value = news.subcategory || ''
    }

    watch(
      () => [token.value, currentPage.value],
      () => {
        if (token.value && currentPage.value === 'recommend') loadInitialRecommendations()
      },
      { immediate: true }
    )
    onMounted(() => {})

    return {
      uploadViewRef,
      token,
      currentUser,
      authTab,
      loginUsername,
      loginPassword,
      regUsername,
      regPassword,
      authError,
      currentPage,
      selectedNews,
      recommendations,
      loading,
      error,
      userProfile,
      profileLoading,
      pieCategoriesLegend,
      userCluster,
      historyList,
      historyLoading,
      historyCount,
      isAdmin,
      searchQ,
      searchCategory,
      searchSubcategory,
      searchItems,
      searchLoading,
      searchError,
      adminOverview,
      adminClusterUsers,
      adminClusterK,
      adminError,
      uploadTitle,
      uploadAbstract,
      uploadBody,
      uploadCategory,
      uploadSubcategory,
      uploadResult,
      onNavigate,
      handleLogin,
      handleRegister,
      handleLogout,
      loadInitialRecommendations,
      openNewsDetail,
      backFromDetail,
      onDetailLike,
      onDetailUnlike,
      goProfile,
      goHistory,
      goAdmin,
      doSearch,
      onLike,
      onUnlike,
      onDislike,
      onUndislike,
      onFavorite,
      onUnfavorite,
      onNotInterested,
      onRemoveNotInterested,
      refreshAdmin,
      rebuildClusters,
      autoRecognize,
      submitUpload,
      handleBatchUpload,
      selectNews,
      feedbackToast,
      batchNewsList,
      selectedNewsIndex
    }
  }
}
</script>

<style scoped>
.feedback-toast {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  padding: 10px 20px;
  background: #1e293b;
  color: #fff;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  z-index: 9999;
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
  animation: toast-in 0.2s ease;
}
@keyframes toast-in {
  from { opacity: 0; transform: translateX(-50%) translateY(8px); }
  to { opacity: 1; transform: translateX(-50%) translateY(0); }
}

#app {
  font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
  background: #f1f5f9;
  min-height: 100vh;
  color: #334155;
}

main {
  padding: 24px 20px;
  max-width: 1100px;
  margin: 0 auto;
  box-sizing: border-box;
}
</style>

<!-- 登录页样式单独写，避免 scoped 导致不生效 -->
<style>
#app .login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 48px);
  padding: 40px 20px;
}

#app .login-card {
  width: 100%;
  max-width: 360px;
  background: #fff;
  border-radius: 12px;
  padding: 32px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
  border: 1px solid #e2e8f0;
}

#app .login-card h2 {
  font-size: 1.25rem;
  color: #1e293b;
  margin-bottom: 20px;
  text-align: center;
}

#app .login-tabs {
  display: flex;
  gap: 0;
  margin-bottom: 20px;
  border-bottom: 1px solid #e2e8f0;
}

#app .login-tab {
  flex: 1;
  padding: 10px 16px;
  font-size: 14px;
  border: none;
  background: transparent;
  color: #64748b;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
}

#app .login-tab:hover {
  color: #1e293b;
}

#app .login-tab.active {
  color: #2563eb;
  font-weight: 600;
  border-bottom-color: #2563eb;
}

#app .login-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

#app .login-form input {
  padding: 12px 14px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 14px;
  background: #f8fafc;
  box-sizing: border-box;
}

#app .login-form input:focus {
  outline: none;
  border-color: #2563eb;
}

#app .login-form .btn-primary {
  padding: 12px;
  font-size: 15px;
  margin-top: 4px;
  background: #2563eb;
  border: none;
  border-radius: 8px;
  color: #fff;
  font-weight: 600;
  cursor: pointer;
}

#app .login-form .btn-primary:hover {
  background: #1d4ed8;
}

#app .login-form .auth-err {
  color: #dc2626;
  font-size: 13px;
  margin: 0;
}
</style>
