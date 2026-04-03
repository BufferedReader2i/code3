<template>
  <main class="profile-page">
    <div class="profile-container">
      <!-- 标题区域 -->
      <div class="profile-header">
        <div class="header-content">
          <div class="header-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/>
              <circle cx="12" cy="7" r="4"/>
            </svg>
          </div>
          <div class="header-text">
            <h2>用户画像</h2>
            <!-- <span class="subtitle">了解您的兴趣偏好</span> -->
          </div>
        </div>
      </div>

      <!-- 加载状态 -->
      <div v-if="profileLoading" class="loading-container">
        <div class="loading-spinner">
          <div class="spinner-ring"></div>
          <div class="spinner-ring"></div>
          <div class="spinner-ring"></div>
        </div>
        <p>正在分析您的兴趣...</p>
      </div>

      <!-- 用户信息内容 -->
      <div v-else-if="userProfile" class="profile-content">
        <!-- 用户群信息 -->
        <!-- <div v-if="userCluster && userCluster.cluster_name" class="cluster-card animate-fade-in">
          <div class="cluster-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
              <path d="M23 21v-2a4 4 0 00-3-3.87"/>
              <path d="M16 3.13a4 4 0 010 7.75"/>
            </svg>
          </div>
          <div class="cluster-info">
            <span class="cluster-label">您属于</span>
            <span class="cluster-pill">
              <span class="cluster-dot"></span>
              {{ userCluster.cluster_name }}
            </span>
          </div>
        </div> -->

        <!-- 聚类图谱 -->
        <!-- <div v-if="clusterGraphNodes.length" class="graph-section animate-fade-in" style="animation-delay: 0.1s">
          <div class="section-header">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <path d="M12 2a10 10 0 010 20"/>
              <path d="M12 2v20"/>
              <path d="M2 12h20"/>
            </svg>
            <h3>兴趣群</h3>
          </div>
          <div ref="graphRef" class="cluster-graph-chart"></div>
        </div> -->
<!--         
        <p v-else-if="userProfile && !profileLoading && userId && !clusterGraphLoading" class="profile-empty animate-fade-in" style="animation-delay: 0.1s">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <path d="M12 16v-4"/>
            <path d="M12 8h.01"/>
          </svg>
          暂无聚类图谱，请由管理员在「管理后台」执行「重算用户群」后刷新
        </p> -->

        <!-- 用户画像饼图 -->
        <!-- 画像更新提示 -->
        <div v-if="profileUpdateNotice" class="profile-update-notice animate-fade-in">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M23 4v6h-6"/>
            <path d="M20.49 15a9 9 0 11-2.12-9.36L23 10"/>
          </svg>
          <span>{{ profileUpdateNotice }}</span>
        </div>

        <!-- 顶部自然语言总结 -->
        <div v-if="profileSummary" class="profile-summary animate-fade-in" style="animation-delay: 0.1s">
          <p>{{ profileSummary }}</p>
        </div>

        <!-- AI画像解读
        <div class="llm-profile-section animate-fade-in" style="animation-delay: 0.15s">
          <div class="section-header">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2a2 2 0 012 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 017 7h1a1 1 0 011 1v3a1 1 0 01-1 1h-1v1a2 2 0 01-2 2H5a2 2 0 01-2-2v-1H2a1 1 0 01-1-1v-3a1 1 0 011-1h1a7 7 0 017-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 012-2z"/>
              <path d="M9 14v2"/>
              <path d="M15 14v2"/>
            </svg>
            <h3>AI画像解读</h3>
          </div>
          <div class="llm-profile-content">
            <div v-if="llmProfileLoading" class="llm-profile-loading">
              <div class="loading-dots">
                <span></span><span></span><span></span>
              </div>
              <span>AI正在分析您的兴趣...</span>
            </div>
            <div v-else-if="llmProfile" class="llm-profile-text">
              <p>{{ llmProfile }}</p>
              <button type="button" class="btn-regenerate" @click="generateLLMProfile" :disabled="llmProfileLoading">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M23 4v6h-6"/>
                  <path d="M20.49 15a9 9 0 11-2.12-9.36L23 10"/>
                </svg>
                重新生成
              </button>
            </div>
            <div v-else class="llm-profile-empty">
              <p>让AI帮您分析阅读兴趣</p>
              <button type="button" class="btn-generate" @click="generateLLMProfile" :disabled="llmProfileLoading">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M12 2a2 2 0 012 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 017 7h1a1 1 0 011 1v3a1 1 0 01-1 1h-1v1a2 2 0 01-2 2H5a2 2 0 01-2-2v-1H2a1 1 0 01-1-1v-3a1 1 0 011-1h1a7 7 0 017-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 012-2z"/>
                </svg>
                生成AI画像
              </button>
            </div>
          </div>
        </div> -->

        <template v-if="userProfile.categories && userProfile.categories.length">
          <div class="profile-section animate-fade-in" style="animation-delay: 0.2s">
            <div class="section-header">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21.21 15.89A10 10 0 118 2.83"/>
                <path d="M22 12A10 10 0 0012 2v10z"/>
              </svg>
              <h3>你的兴趣方向</h3>
            </div>
            <div class="profile-pie-wrap">
              <div ref="chartRef" class="profile-pie-chart"></div>
              <ul class="profile-legend">
                <li v-for="item in pieCategoriesLegend" :key="'cat-'+item.name" class="profile-legend-item">
                  <span class="legend-dot" :style="{ background: item.color }"></span>
                  <span class="legend-name">{{ item.name }}</span>
                  <span class="legend-score">{{ formatScore(item.score) }}%</span>
                </li>
              </ul>
            </div>
          </div>
        </template>

        <!-- 兴趣标签 -->
        <template v-if="filteredSubcategories.length">
          <div class="tags-section animate-fade-in" style="animation-delay: 0.3s">
            <div class="section-header">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M20.59 13.41l-7.17 7.17a2 2 0 01-2.83 0L2 12V2h10l8.59 8.59a2 2 0 010 2.82z"/>
                <line x1="7" y1="7" x2="7.01" y2="7"/>
              </svg>
              <h3>你最近关注的话题</h3>
            </div>
            <div class="profile-tags">
              <div
                v-for="s in filteredSubcategories"
                :key="'sub-'+s.name"
                class="tag-square"
                :class="{ strong: s.strength === 'strong', medium: s.strength === 'medium' }"
              >
                <span>{{ s.name }}</span>
                <button type="button" class="tag-delete" @click="deleteSubcategory(s.name)" title="删除标签">×</button>
              </div>
            </div>
          </div>
        </template>

        <p v-if="!userProfile.history_count && !(userProfile.categories && userProfile.categories.length) && !filteredSubcategories.length" class="profile-empty animate-fade-in" style="animation-delay: 0.2s">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
            <polyline points="14,2 14,8 20,8"/>
          </svg>
          暂无画像数据，多浏览新闻后会自动生成
        </p>
      </div>
    </div>
  </main>
</template>

<script>
import { ref, watch, onMounted, onBeforeUnmount, nextTick, computed } from 'vue'
import * as echarts from 'echarts'
import { formatScore } from '../utils/pieChart'
import { api } from '../api'

export default {
  name: 'ProfileView',
  props: {
    userId: { type: String, default: '' },
    userProfile: { type: Object, default: null },
    profileLoading: { type: Boolean, default: false },
    pieCategoriesLegend: { type: Array, default: () => [] },
    userCluster: { type: Object, default: null },
    // 新增：自然语言总结和更新提示
    profileSummary: { type: String, default: '' },
    profileUpdateNotice: { type: String, default: '' }
  },
  setup(props) {
    const chartRef = ref(null)
    const graphRef = ref(null)
    let chart = null
    let graphChart = null
    const clusterGraphNodes = ref([])
    const clusterGraphLinks = ref([])
    const clusterGraphLoading = ref(false)
    
    // LLM画像相关
    const llmProfile = ref('')
    const llmProfileLoading = ref(false)
    
    // 加载已保存的LLM画像
    const loadLLMProfile = () => {
      if (!props.userId) {
        // 用户ID为空时清空画像
        llmProfile.value = ''
        return
      }
      const key = `llmProfile_${props.userId}`
      const saved = localStorage.getItem(key)
      // 无论是否有保存值，都要更新（清空或设置新值）
      llmProfile.value = saved || ''
    }
    
    // 保存LLM画像到localStorage
    const saveLLMProfile = () => {
      if (!props.userId || !llmProfile.value) return
      const key = `llmProfile_${props.userId}`
      localStorage.setItem(key, llmProfile.value)
    }
    
    // 已删除的标签列表（会话期间）
    const deletedSubcategories = ref([])
    
    // 加载已删除标签
    const loadDeletedSubcategories = () => {
      if (!props.userId) return
      const key = `deletedSubcategories_${props.userId}`
      const saved = localStorage.getItem(key)
      deletedSubcategories.value = saved ? JSON.parse(saved) : []
    }
    
    // 保存已删除标签到 localStorage
    const saveDeletedSubcategories = () => {
      if (!props.userId) return
      const key = `deletedSubcategories_${props.userId}`
      localStorage.setItem(key, JSON.stringify(deletedSubcategories.value))
    }
    
    // 过滤已删除的标签（计算属性）
    const filteredSubcategories = computed(() => {
      if (!props.userProfile || !props.userProfile.subcategories) return []
      return props.userProfile.subcategories.filter(s => 
        !deletedSubcategories.value.includes(s.name)
      )
    })

    function initChart() {
      if (!chartRef.value || !props.pieCategoriesLegend.length) return
      if (chart) {
        chart.dispose()
        chart = null
      }
      chart = echarts.init(chartRef.value)
      updateChart()
    }

    function updateChart() {
      if (!chart || !props.pieCategoriesLegend.length) return
      const data = props.pieCategoriesLegend.map((item) => ({
        name: item.name,
        value: Math.max(0, Number(item.score) || 0) * 100
      }))
      const colors = props.pieCategoriesLegend.map(item => item.color)
      chart.setOption({
        color: colors,
        tooltip: {
          trigger: 'item',
          backgroundColor: 'rgba(30, 41, 59, 0.9)',
          borderColor: 'transparent',
          borderRadius: 8,
          padding: [10, 14],
          textStyle: { color: '#fff', fontSize: 12 },
          formatter: (params) => `${params.name}: ${Number(params.value).toFixed(2)}%`
        },
        series: [
          {
            type: 'pie',
            radius: ['45%', '72%'],
            center: ['50%', '50%'],
            avoidLabelOverlap: false,
            itemStyle: {
              borderColor: '#fff',
              borderWidth: 2,
              borderRadius: 6
            },
            label: { show: false },
            emphasis: {
              scale: true,
              scaleSize: 8,
              label: { show: false },
              itemStyle: {
                shadowBlur: 15,
                shadowColor: 'rgba(0,0,0,0.15)'
              }
            },
            data,
            animationType: 'scale',
            animationDuration: 800,
            animationEasing: 'elasticOut'
          }
        ]
      })
    }

    const onResize = () => {
      chart?.resize()
      graphChart?.resize()
    }

    function initGraphChart() {
      if (!clusterGraphNodes.value.length) return
      if (!graphRef.value) return
      if (graphChart) {
        graphChart.dispose()
        graphChart = null
      }
      graphChart = echarts.init(graphRef.value)
      const categoryColors = ['#6366f1', '#0d9488', '#94a3b8']
      const nodes = clusterGraphNodes.value.map((n) => ({
        id: n.id,
        name: n.name,
        category: n.category,
        symbolSize: n.category === 0 ? 45 : n.category === 1 ? 60 : 30,
        itemStyle: {
          color: categoryColors[n.category],
          shadowBlur: 10,
          shadowColor: 'rgba(0,0,0,0.2)'
        }
      }))
      const links = clusterGraphLinks.value.map((l) => ({ source: l.source, target: l.target }))
      const categories = [
        { name: '当前用户', itemStyle: { color: categoryColors[0] } },
        { name: '兴趣群', itemStyle: { color: categoryColors[1] } },
        { name: '同群用户', itemStyle: { color: categoryColors[2] } }
      ]
      graphChart.setOption({
        tooltip: {
          formatter: (p) => (p.data ? p.data.name : ''),
          backgroundColor: 'rgba(30, 41, 59, 0.9)',
          borderColor: 'transparent',
          borderRadius: 8,
          textStyle: { color: '#fff' }
        },
        legend: {
          data: categories.map((c) => c.name),
          bottom: 10,
          textStyle: { color: '#64748b' }
        },
        series: [
          {
            type: 'graph',
            layout: 'force',
            data: nodes,
            links,
            categories,
            roam: true,
            label: { 
              show: true, 
              position: 'right', 
              formatter: '{b}',
              color: '#475569',
              fontSize: 11
            },
            labelLayout: { hideOverlap: true },
            scaleLimit: { min: 0.4, max: 2 },
            force: {
              repulsion: 220,
              edgeLength: nodes.length === 1 ? [] : [80, 150],
              gravity: 0.05
            },
            lineStyle: { color: 'source', curveness: 0.2, width: 1.5 },
            emphasis: {
              focus: 'adjacency',
              lineStyle: { width: 3 }
            }
          }
        ]
      })
    }

    async function loadClusterGraph() {
      if (!props.userId) {
        clusterGraphNodes.value = []
        clusterGraphLinks.value = []
        return
      }
      clusterGraphLoading.value = true
      try {
        const res = await api.getUserClusterGraph(props.userId, 30)
        clusterGraphNodes.value = res.data?.nodes || []
        clusterGraphLinks.value = res.data?.links || []
        nextTick(() => {
          nextTick(() => initGraphChart())
        })
      } catch (_) {
        clusterGraphNodes.value = []
        clusterGraphLinks.value = []
      } finally {
        clusterGraphLoading.value = false
      }
    }

    async function deleteSubcategory(subcategoryName) {
      try {
        // 调用 API 删除标签
        await api.deleteUserSubcategory(props.userId, subcategoryName)
        
        // 添加到已删除列表
        if (!deletedSubcategories.value.includes(subcategoryName)) {
          deletedSubcategories.value.push(subcategoryName)
          saveDeletedSubcategories()
        }
        
        // 如果 userProfile 是通过 props 传递的，我们不能直接修改它
        // 这里我们只是更新已删除标签列表，filteredSubcategories 会自动更新
        console.log(`标签 "${subcategoryName}" 已删除，将在本次会话中过滤`)
      } catch (err) {
        console.error('删除标签失败:', err)
      }
    }

    onMounted(() => {
      window.addEventListener('resize', onResize)
      nextTick(() => {
        if (chartRef.value && props.pieCategoriesLegend.length) initChart()
      })
      if (props.userId) loadClusterGraph()
      
      // 加载已删除的标签
      loadDeletedSubcategories()
      // 加载已保存的LLM画像
      loadLLMProfile()
    })

    onBeforeUnmount(() => {
      window.removeEventListener('resize', onResize)
      chart?.dispose()
      chart = null
      graphChart?.dispose()
      graphChart = null
    })

    watch(
      () => props.pieCategoriesLegend,
      (val) => {
        if (!val?.length) return
        nextTick(() => {
          if (!chartRef.value) return
          if (!chart) initChart()
          else updateChart()
        })
      },
      { deep: true, immediate: true }
    )

    watch(
      () => props.userId,
      (uid) => {
        if (uid) loadClusterGraph()
        // 用户 ID 变化时重新加载已删除标签和LLM画像
        loadDeletedSubcategories()
        loadLLMProfile()
      },
      { immediate: true }
    )

    watch(
      () => [clusterGraphNodes.value.length, clusterGraphLinks.value.length],
      () => {
        nextTick(() => {
          nextTick(() => initGraphChart())
        })
      },
      { deep: true }
    )

    // 自然语言总结（从 props 获取，由 App.vue 计算后传入）
    const profileSummary = computed(() => props.profileSummary)
    const profileUpdateNotice = computed(() => props.profileUpdateNotice)
    
    // 生成LLM画像
    async function generateLLMProfile() {
      if (!props.userId || llmProfileLoading.value) return
      llmProfileLoading.value = true
      try {
        const res = await api.getLLMProfile(props.userId)
        llmProfile.value = res.data.llm_profile
        // 保存到localStorage
        saveLLMProfile()
      } catch (err) {
        console.error('生成LLM画像失败:', err)
        llmProfile.value = '生成失败，请稍后重试'
      } finally {
        llmProfileLoading.value = false
      }
    }
    
    return {
      chartRef,
      graphRef,
      formatScore,
      clusterGraphNodes,
      clusterGraphLinks,
      clusterGraphLoading,
      deleteSubcategory,
      filteredSubcategories,
      profileSummary,
      profileUpdateNotice,
      llmProfile,
      llmProfileLoading,
      generateLLMProfile
    }
  }
}
</script>

<style scoped>
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.profile-page { 
  max-width: 1200px; 
  margin: 0 auto; 
  box-sizing: border-box; 
}

.profile-container {
  background: #fff;
  padding: 32px;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  border: 1px solid #e2e8f0;
}

/* 标题 */
.profile-header {
  margin-bottom: 28px;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon {
  width: 52px;
  height: 52px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 6px 16px rgba(99, 102, 241, 0.35);
}

.header-icon svg {
  width: 26px;
  height: 26px;
  color: #fff;
}

.header-text h2 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 700;
  color: #1e293b;
  font-family: 'Inter', system-ui, sans-serif;
}

.header-text .subtitle {
  font-size: 13px;
  color: #64748b;
}

/* 画像更新提示条 */
.profile-update-notice {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 18px;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border: 1px solid #bae6fd;
  border-radius: 10px;
  margin-bottom: 20px;
  color: #0369a1;
  font-size: 14px;
  font-weight: 500;
}

.profile-update-notice svg {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 顶部自然语言总结 */
.profile-summary {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 20px 24px;
  margin-bottom: 24px;
}

.profile-summary p {
  margin: 0;
  font-size: 15px;
  line-height: 1.7;
  color: #334155;
}

.animate-fade-in {
  animation: fadeIn 0.5s ease forwards;
  opacity: 0;
}

/* 加载状态 */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
}

.loading-spinner {
  position: relative;
  width: 50px;
  height: 50px;
  margin-bottom: 16px;
}

.spinner-ring {
  position: absolute;
  width: 100%;
  height: 100%;
  border: 3px solid transparent;
  border-top-color: #6366f1;
  border-radius: 50%;
  animation: spin 1.2s linear infinite;
}

.spinner-ring:nth-child(2) {
  width: 75%;
  height: 75%;
  top: 12.5%;
  left: 12.5%;
  border-top-color: #8b5cf6;
  animation-duration: 1s;
  animation-direction: reverse;
}

.spinner-ring:nth-child(3) {
  width: 50%;
  height: 50%;
  top: 25%;
  left: 25%;
  border-top-color: #a78bfa;
  animation-duration: 0.8s;
}

.loading-container p {
  color: #64748b;
  font-size: 14px;
  margin: 0;
}

.profile-content { 
  margin-top: 8px; 
}

/* 用户群卡片 */
.cluster-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 18px 20px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border-radius: 14px;
  margin-bottom: 24px;
  box-shadow: 0 6px 16px rgba(99, 102, 241, 0.35);
}

.cluster-icon {
  width: 48px;
  height: 48px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.cluster-icon svg {
  width: 24px;
  height: 24px;
  color: #fff;
}

.cluster-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.cluster-label {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.8);
}

.cluster-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
  padding: 8px 16px;
  border-radius: 25px;
  font-size: 15px;
  font-weight: 600;
  backdrop-filter: blur(10px);
}

.cluster-dot {
  width: 8px;
  height: 8px;
  background: #a5f3fc;
  border-radius: 50%;
  animation: pulse 2s ease infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.7; transform: scale(1.2); }
}

/* 区块标题 */
.section-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f1f5f9;
}

.section-header svg {
  width: 22px;
  height: 22px;
  color: #6366f1;
}

.section-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}

/* 聚类图谱 */
.graph-section {
  margin-bottom: 28px;
}

.cluster-graph-chart { 
  width: 100%; 
  height: 400px; 
  min-height: 320px;
  border-radius: 12px;
  background: #fafbfc;
}

/* 饼图区域 */
.profile-section {
  margin-bottom: 28px;
}

.profile-pie-wrap {
  display: flex;
  align-items: center;
  gap: 32px;
  padding: 20px;
  background: #fafbfc;
  border-radius: 14px;
}

.profile-pie-chart {
  width: 220px;
  height: 220px;
  min-width: 220px;
  min-height: 220px;
  flex-shrink: 0;
}

.profile-legend {
  list-style: none;
  margin: 0;
  padding: 0;
  flex: 1;
}

.profile-legend-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid #f1f5f9;
}

.profile-legend-item:last-child {
  border-bottom: none;
}

.legend-dot {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.legend-name {
  flex: 1;
  font-size: 14px;
  color: #475569;
  font-weight: 500;
}

.legend-score {
  font-size: 14px;
  font-weight: 700;
  color: #6366f1;
}

/* 标签区域 */
.tags-section {
  margin-bottom: 20px;
}

.profile-tags { 
  display: flex; 
  flex-wrap: wrap; 
  gap: 10px;
  padding: 20px;
  background: #fafbfc;
  border-radius: 14px;
}

.tag-square {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 10px;
  font-size: 14px;
  background: #fff;
  color: #475569;
  border: 1px solid #e2e8f0;
  font-weight: 500;
  transition: all 0.2s ease;
}

.tag-delete {
  background: none;
  border: none;
  color: #94a3b8;
  font-size: 18px;
  cursor: pointer;
  padding: 0;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s ease;
}

.tag-delete:hover {
  color: #ef4444;
}

.tag-square:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.08);
}

.tag-square.strong {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: #fff;
  border-color: transparent;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.35);
}

.tag-square.medium {
  background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%);
  color: #4f46e5;
  border-color: transparent;
}

/* 空状态 */
.profile-empty {
  font-size: 14px;
  color: #94a3b8;
  margin-top: 12px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px;
  background: #fafbfc;
  border-radius: 12px;
}

.profile-empty svg {
  width: 22px;
  height: 22px;
  color: #94a3b8;
  flex-shrink: 0;
}

/* AI画像解读 */
.llm-profile-section {
  background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
  border: 1px solid #bbf7d0;
  border-radius: 14px;
  padding: 20px;
  margin-bottom: 24px;
}

.llm-profile-section .section-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.llm-profile-section .section-header svg {
  width: 22px;
  height: 22px;
  color: #16a34a;
}

.llm-profile-section .section-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #166534;
}

.llm-profile-content {
  min-height: 60px;
}

.llm-profile-loading {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #64748b;
  font-size: 14px;
}

.loading-dots {
  display: flex;
  gap: 4px;
}

.loading-dots span {
  width: 8px;
  height: 8px;
  background: #22c55e;
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.loading-dots span:nth-child(1) { animation-delay: -0.32s; }
.loading-dots span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.llm-profile-text p {
  margin: 0 0 12px 0;
  font-size: 14px;
  line-height: 1.6;
  color: #374151;
}

.btn-regenerate {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: #fff;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 13px;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-regenerate:hover {
  background: #f9fafb;
  border-color: #9ca3af;
}

.btn-regenerate svg {
  width: 14px;
  height: 14px;
}

.btn-regenerate:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.llm-profile-empty {
  text-align: center;
  padding: 10px 0;
}

.llm-profile-empty p {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #6b7280;
}

.btn-generate {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  color: #fff;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 12px rgba(34, 197, 94, 0.35);
}

.btn-generate:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(34, 197, 94, 0.4);
}

.btn-generate svg {
  width: 18px;
  height: 18px;
}

.btn-generate:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

@media (max-width: 768px) {
  .profile-pie-wrap {
    flex-direction: column;
  }
  
  .profile-pie-chart {
    width: 180px;
    height: 180px;
  }
}
</style>
