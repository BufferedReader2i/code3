<template>
  <main class="admin-page">
    <div class="admin-container">
      <!-- 标题区域 -->
      <div class="title-row">
        <div class="title-group">
          <div class="title-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="7" height="9" rx="1"/>
              <rect x="14" y="3" width="7" height="5" rx="1"/>
              <rect x="14" y="12" width="7" height="9" rx="1"/>
              <rect x="3" y="16" width="7" height="5" rx="1"/>
            </svg>
          </div>
          <h2>数据后台</h2>
        </div>
        <div class="actions">
          <button type="button" class="btn-secondary" @click="$emit('refresh')">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 12a9 9 0 11-9-9"/>
              <polyline points="21,3 21,9 15,9"/>
            </svg>
            刷新数据
          </button>
          <!-- <button type="button" class="btn-primary" @click="$emit('rebuild-clusters')">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 2v6h-6"/>
              <path d="M3 12a9 9 0 0115-6.7L21 8"/>
              <path d="M3 22v-6h6"/>
              <path d="M21 12a9 9 0 01-15 6.7L3 16"/>
            </svg>
            重算用户群
          </button> -->
        </div>
      </div>

      <div v-if="error" class="error animate-shake">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        {{ error }}
      </div>

      <!-- 24小时统计卡片 -->
      <section class="cards">
        <div class="card card-gradient-1 animate-fade-in" style="animation-delay: 0.1s">
          <div class="card-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
              <path d="M23 21v-2a4 4 0 00-3-3.87"/>
              <path d="M16 3.13a4 4 0 010 7.75"/>
            </svg>
          </div>
          <div class="card-content">
            <div class="k">活跃用户数(24h)</div>
            <div class="v" :data-value="overview?.dau ?? 0">{{ formatNumber(overview?.dau) }}</div>
          </div>
          <div class="card-decoration"></div>
        </div>
        
        <div class="card card-gradient-2 animate-fade-in" style="animation-delay: 0.2s">
          <div class="card-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
            </svg>
          </div>
          <div class="card-content">
            <div class="k">用户交互事件数量(24h)</div>
            <div class="v" :data-value="overview?.events_24h ?? 0">{{ formatNumber(overview?.events_24h) }}</div>
          </div>
          <div class="card-decoration"></div>
        </div>
      </section>

      <!-- 趋势图表区域 -->
      <section class="charts-row">
        <div class="chart-card animate-fade-in" style="animation-delay: 0.3s">
          <div class="chart-header">
            <span class="chart-title">近7天活跃用户数</span>
            
          </div>
          <LineChart
            :data="overview?.dau_trend || []"
            color="#6366f1"
          />
        </div>
        <div class="chart-card animate-fade-in" style="animation-delay: 0.4s">
          <div class="chart-header">
            <span class="chart-title">用户交互事件数量</span>
            
          </div>
          <LineChart
            :data="overview?.events_trend || []"
            color="#f59e0b"
          />
        </div>
      </section>
<!--         
        <div class="card card-gradient-3 animate-fade-in" style="animation-delay: 0.5s">
          <div class="card-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="3"/>
              <path d="M12 1v6m0 6v10"/>
              <path d="M21 12h-6m-6 0H1"/>
            </svg>
          </div>
          <div class="card-content">
            <div class="k">兴趣群数量</div>
            <div class="v cluster-text">{{ clusterInfo }}</div>
          </div>
          <div class="card-decoration"></div>
        </div> -->

      <!-- 类别和新闻图表 -->
      <section class="split">
        <div class="panel animate-fade-in" style="animation-delay: 0.6s">
          <PieChart 
            :data="overview?.top_categories_7d || []" 
            title="近7天 Top 类别"
            name-key="name"
            value-key="count"
          />
        </div>
        <div class="panel animate-fade-in" style="animation-delay: 0.7s">
          <BarChart 
            :data="overview?.top_news_7d || []" 
            title="近7天 Top 新闻"
            name-key="title"
            value-key="count"
          />
        </div>
      </section>
    </div>
  </main>
</template>

<script>
import LineChart from './charts/LineChart.vue'
import PieChart from './charts/PieChart.vue'
import BarChart from './charts/BarChart.vue'

export default {
  name: 'AdminView',
  components: {
    LineChart,
    PieChart,
    BarChart
  },
  props: {
    overview: { type: Object, default: null },
    clusterUsers: { type: Number, default: 0 },
    clusterK: { type: Number, default: 0 },
    error: { type: String, default: '' }
  },
  emits: [
    'refresh', 'rebuild-clusters'
  ],
  computed: {
    clusterInfo() {
      if (!this.clusterUsers) return '-'
      return `${this.clusterUsers} / ${this.clusterK}`
    }
  },
  methods: {
    formatNumber(num) {
      if (!num && num !== 0) return '-'
      return num.toLocaleString()
    }
  }
}
</script>

<style scoped>
/* 基础动画 */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-5px); }
  75% { transform: translateX(5px); }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

.animate-fade-in {
  animation: fadeIn 0.5s ease forwards;
  opacity: 0;
}

.animate-shake {
  animation: shake 0.4s ease;
}

/* 页面容器 */
.admin-page { 
  max-width: 1200px; 
  margin: 0 auto; 
  box-sizing: border-box;
}

.admin-container {
  background: #fff;
  padding: 28px 32px;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  border: 1px solid #e2e8f0;
}

/* 标题区域 */
.title-row { 
  display: flex; 
  align-items: center; 
  justify-content: space-between; 
  gap: 16px; 
  flex-wrap: wrap;
  margin-bottom: 8px;
}

.title-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-icon {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.title-icon svg {
  width: 20px;
  height: 20px;
  color: #fff;
}

.title-row h2 { 
  margin: 0; 
  font-size: 1.5rem; 
  font-weight: 700; 
  color: #1e293b;
  font-family: 'Inter', system-ui, sans-serif;
}

.actions { 
  display: inline-flex; 
  gap: 12px; 
}

/* 按钮样式 */
.btn-primary, .btn-secondary, .btn-search {
  padding: 10px 18px;
  border: none;
  border-radius: 10px;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s ease;
}

.btn-primary {
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
  color: #fff;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.35);
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(99, 102, 241, 0.45);
}

.btn-secondary {
  background: #f8fafc;
  color: #475569;
  border: 1px solid #e2e8f0;
}

.btn-secondary:hover {
  background: #f1f5f9;
  border-color: #cbd5e1;
  transform: translateY(-2px);
}

.btn-search {
  background: linear-gradient(135deg, #0d9488 0%, #0f766e 100%);
  color: #fff;
  box-shadow: 0 4px 12px rgba(13, 148, 136, 0.3);
}

.btn-search:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(13, 148, 136, 0.4);
}

.btn-primary svg, .btn-secondary svg, .btn-search svg {
  width: 16px;
  height: 16px;
}

/* 错误提示 */
.error {
  display: flex;
  align-items: center;
  gap: 10px;
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
  color: #dc2626;
  padding: 14px 18px;
  border-radius: 12px;
  margin-top: 16px;
  border: 1px solid #fecaca;
  font-size: 14px;
}

.error svg {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

/* 图表区域 */
.charts-row { 
  display: grid; 
  grid-template-columns: 1fr 1fr; 
  gap: 20px; 
  margin-top: 24px; 
}

.chart-card { 
  border: 1px solid #e2e8f0; 
  border-radius: 16px; 
  padding: 0;
  background: linear-gradient(180deg, #fafbfc 0%, #fff 100%);
  overflow: hidden;
  transition: all 0.3s ease;
}

.chart-card:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

.chart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px 0;
}

.chart-title {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}

.chart-badge {
  font-size: 12px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 20px;
}

.trend-up {
  background: #ecfdf5;
  color: #059669;
}

.trend-down {
  background: #fef2f2;
  color: #dc2626;
}

/* 统计卡片 */
.cards { 
  display: grid; 
  grid-template-columns: repeat(3, 1fr); 
  gap: 20px; 
  margin-top: 20px; 
}

.card { 
  border-radius: 16px; 
  padding: 20px;
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 16px;
}

.card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.1);
}

.card-icon {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.card-icon svg {
  width: 26px;
  height: 26px;
}

.card-content {
  flex: 1;
  z-index: 1;
}

.card .k { 
  font-size: 13px; 
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 6px;
  font-weight: 500;
}

.card .v { 
  font-size: 26px; 
  font-weight: 700; 
  color: #fff;
  font-family: 'Inter', system-ui, sans-serif;
}

.card .cluster-text {
  font-size: 18px;
}

.card-decoration {
  position: absolute;
  top: -50%;
  right: -50%;
  width: 100%;
  height: 200%;
  background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
  pointer-events: none;
}

.card-gradient-1 {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  box-shadow: 0 8px 24px rgba(99, 102, 241, 0.35);
}

.card-gradient-1 .card-icon {
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
}

.card-gradient-2 {
  background: linear-gradient(135deg, #f59e0b 0%, #f97316 100%);
  box-shadow: 0 8px 24px rgba(245, 158, 11, 0.35);
}

.card-gradient-2 .card-icon {
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
}

.card-gradient-3 {
  background: linear-gradient(135deg, #0d9488 0%, #14b8a6 100%);
  box-shadow: 0 8px 24px rgba(13, 148, 136, 0.35);
}

.card-gradient-3 .card-icon {
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
}

/* 面板 */
.split { 
  display: grid; 
  grid-template-columns: 1fr 1fr; 
  gap: 20px; 
  margin-top: 20px; 
}

.panel { 
  border: 1px solid #e2e8f0; 
  border-radius: 16px; 
  padding: 0; 
  margin-top: 0;
  overflow: hidden;
  background: #fff;
}

.panel h3 {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0;
  padding: 20px 20px 0;
  font-size: 15px;
  color: #0f172a;
}

.panel h3 svg {
  width: 20px;
  height: 20px;
  color: #6366f1;
}

/* 新闻管理面板 */
.news-panel {
  margin-top: 20px;
  padding-bottom: 20px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 20px 16px;
  border-bottom: 1px solid #f1f5f9;
  margin-bottom: 16px;
}

.panel-header h3 {
  padding: 0;
  border: none;
}

.news-count {
  font-size: 13px;
  color: #64748b;
  background: #f8fafc;
  padding: 6px 12px;
  border-radius: 20px;
}

/* 筛选区域 */
.filters { 
  display: flex; 
  gap: 12px; 
  flex-wrap: wrap; 
  align-items: center;
  padding: 0 20px;
}

.search-wrapper {
  position: relative;
  flex: 1;
  min-width: 180px;
}

.search-wrapper svg {
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  width: 18px;
  height: 18px;
  color: #94a3b8;
}

.search-wrapper input {
  width: 100%;
  padding: 12px 14px 12px 44px;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  font-size: 14px;
  background: #f8fafc;
  box-sizing: border-box;
  transition: all 0.2s ease;
}

.search-wrapper input:focus {
  outline: none;
  border-color: #6366f1;
  background: #fff;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.filters select {
  padding: 12px 36px 12px 14px;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  font-size: 14px;
  background: #f8fafc url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%2394a3b8' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E") no-repeat right 12px center;
  appearance: none;
  cursor: pointer;
  transition: all 0.2s ease;
}

.filters select:focus {
  outline: none;
  border-color: #6366f1;
  background-color: #fff;
}

/* 表格样式 */
.table-wrap { 
  overflow-x: auto; 
  padding: 0 20px;
}

.table { 
  width: 100%; 
  border-collapse: collapse; 
  min-width: 700px;
}

.table th, .table td { 
  text-align: left; 
  padding: 14px 12px; 
  border-bottom: 1px solid #f1f5f9; 
  font-size: 14px; 
  color: #475569;
  vertical-align: middle;
}

.table thead th {
  background: #f8fafc;
  font-weight: 600;
  color: #1e293b;
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.table tbody tr {
  transition: all 0.2s ease;
  animation: fadeIn 0.4s ease forwards;
  opacity: 0;
}

.table tbody tr:hover {
  background: linear-gradient(90deg, #f8fafc 0%, #fff 100%);
  transform: scale(1.01);
}

.mono { 
  font-family: 'SF Mono', 'Fira Code', monospace; 
  font-size: 12px; 
  color: #64748b;
}

.title { 
  max-width: 300px; 
  white-space: nowrap; 
  overflow: hidden; 
  text-overflow: ellipsis;
  font-weight: 500;
  color: #1e293b;
}

.category-tag {
  background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%);
  color: #4338ca;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}

/* 状态标签 */
.pill { 
  display: inline-flex; 
  align-items: center; 
  gap: 6px;
  padding: 6px 12px;
  border-radius: 20px; 
  font-size: 12px; 
  font-weight: 500;
}

.pill.active { 
  background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
  color: #059669;
}

.pill.inactive { 
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
  color: #dc2626;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

/* 操作按钮 */
.btn-mini { 
  padding: 8px 14px;
  border-radius: 8px; 
  border: 1px solid #e2e8f0; 
  background: #fff; 
  cursor: pointer; 
  font-size: 12px;
  font-weight: 500;
  transition: all 0.2s ease;
}

.btn-mini:hover { 
  background: #f8fafc;
  border-color: #6366f1;
  color: #6366f1;
}

.btn-mini.btn-danger:hover {
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
  border-color: #dc2626;
  color: #dc2626;
}

/* 骨架屏 */
.skeleton-table {
  padding: 0 20px;
}

.skeleton-row {
  display: flex;
  gap: 12px;
  padding: 14px 0;
  border-bottom: 1px solid #f1f5f9;
}

.skeleton-row.header {
  background: #f8fafc;
  margin: 0 -20px;
  padding: 14px 20px;
  border-bottom: 1px solid #e2e8f0;
}

.skeleton-item {
  height: 14px;
  background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
}

.skeleton-row.header .skeleton-item {
  background: linear-gradient(90deg, #e2e8f0 25%, #cbd5e1 50%, #e2e8f0 75%);
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #64748b;
}

.empty-icon {
  width: 80px;
  height: 80px;
  margin: 0 auto 20px;
  background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-icon svg {
  width: 40px;
  height: 40px;
  color: #94a3b8;
}

.empty-state p {
  margin: 0 0 8px;
  font-size: 16px;
  font-weight: 600;
  color: #475569;
}

.empty-state span {
  font-size: 14px;
  color: #94a3b8;
}

/* 响应式 */
@media (max-width: 1024px) {
  .charts-row { grid-template-columns: 1fr; }
  .cards { grid-template-columns: 1fr; }
  .split { grid-template-columns: 1fr; }
}

@media (max-width: 640px) {
  .admin-container {
    padding: 20px;
    border-radius: 12px;
  }
  
  .title-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .filters {
    flex-direction: column;
  }
  
  .search-wrapper {
    width: 100%;
  }
  
  .filters select, .btn-search {
    width: 100%;
  }
  
  .card .v {
    font-size: 22px;
  }
}
</style>
