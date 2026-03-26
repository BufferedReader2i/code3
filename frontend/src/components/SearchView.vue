<template>
  <main class="search-page">
    <div class="search-container">
      <!-- 标题区域 -->
      <div class="search-header">
        <div class="header-content">
          <div class="header-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8"/>
              <path d="m21 21-4.35-4.35"/>
            </svg>
          </div>
          <div class="header-text">
            <h2>搜索发现</h2>
            
          </div>
        </div>
      </div>

      <!-- 搜索表单 -->
      <div class="search-form">
        <div class="search-input-wrapper main-input">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/>
            <path d="m21 21-4.35-4.35"/>
          </svg>
          <input
            :value="q"
            type="text"
            placeholder="搜索标题或标签..."
            @input="$emit('update:q', $event.target.value)"
            @keyup.enter="$emit('search')"
          >
        </div>
        <div class="search-row">
          <div class="search-input-wrapper">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="7" height="7"/>
              <rect x="14" y="3" width="7" height="7"/>
              <rect x="14" y="14" width="7" height="7"/>
              <rect x="3" y="14" width="7" height="7"/>
            </svg>
            <select
              :value="category"
              @change="$emit('update:category', $event.target.value)"
            >
              <option value="">全部类别</option>
              <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
            </select>
          </div>
        </div>
        <button type="button" class="btn-search" @click="$emit('search')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/>
            <path d="m21 21-4.35-4.35"/>
          </svg>
          搜索
        </button>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="loading">
        <div class="loading-dots">
          <span></span>
          <span></span>
          <span></span>
        </div>
        <p>正在搜索...</p>
      </div>
      
      <!-- 错误提示 -->
      <div v-if="error" class="error">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        {{ error }}
      </div>

      <!-- 搜索结果 -->
      <div v-if="items && items.length" class="result-section">
        <div class="result-header">
          <span class="result-count">找到 <strong>{{ items.length }}</strong> 条相关内容</span>
        </div>
        <div class="result-grid">
          <div
            v-for="(n, index) in items"
            :key="n.id"
            class="result-card"
            :style="{ animationDelay: `${index * 0.08}s` }"
            @click="$emit('open', n)"
          >
            <div class="card-header">
              <span class="badge">{{ n.category }}</span>
              <span v-if="n.subcategory" class="sub-badge">{{ n.subcategory }}</span>
            </div>
            <h4>{{ n.title }}</h4>
            <p v-if="n.abstract">{{ n.abstract }}</p>
            <div class="card-footer">
              <span class="news-id">ID: {{ n.id }}</span>
              <span class="view-text">查看详情</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else-if="!loading" class="empty-tip">
        <div class="empty-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <circle cx="11" cy="11" r="8"/>
            <path d="m21 21-4.35-4.35"/>
            <path d="M8 11h6"/>
          </svg>
        </div>
        
      </div>
    </div>
  </main>
</template>

<script>
import { api } from '../api.js'

export default {
  name: 'SearchView',
  props: {
    q: { type: String, default: '' },
    category: { type: String, default: '' },
    items: { type: Array, default: () => [] },
    loading: { type: Boolean, default: false },
    error: { type: String, default: '' }
  },
  data() {
    return {
      categories: [],
      categoriesLoading: false
    }
  },
  emits: ['update:q', 'update:category', 'search', 'open'],
  mounted() {
    this.loadCategories()
  },
  methods: {
    async loadCategories() {
      this.categoriesLoading = true
      try {
        const res = await api.getNewsCategories()
        this.categories = res.data.categories || []
      } catch (err) {
        console.error('Failed to load categories:', err)
        this.categories = []
      } finally {
        this.categoriesLoading = false
      }
    }
  }
}
</script>

<style scoped>
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(15px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-3px); }
}

.search-page { 
  max-width: 1200px; 
  margin: 0 auto; 
  box-sizing: border-box; 
}

.search-container {
  background: #fff;
  padding: 32px;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  border: 1px solid #e2e8f0;
}

/* 标题 */
.search-header {
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

/* 搜索表单 */
.search-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-bottom: 24px;
}

.search-input-wrapper {
  position: relative;
  flex: 1;
}

.search-input-wrapper svg {
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  width: 20px;
  height: 20px;
  color: #94a3b8;
}

.search-input-wrapper.main-input svg {
  width: 22px;
  height: 22px;
}

.search-input-wrapper input,
.search-input-wrapper select {
   width: 100%;
   padding: 14px 16px 14px 48px;
   border: 2px solid #e2e8f0;
   border-radius: 12px;
   font-size: 15px;
   background: #f8fafc;
   box-sizing: border-box;
   transition: all 0.2s ease;
 }

.search-input-wrapper select {
   appearance: none;
   background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%2394a3b8' d='M6 9L1 4h10z'/%3E%3C/svg%3E");
   background-repeat: no-repeat;
   background-position: right 16px center;
   padding-right: 40px;
 }

.search-input-wrapper.main-input input {
  padding: 16px 16px 16px 54px;
  font-size: 16px;
}

.search-input-wrapper input:focus {
  outline: none;
  border-color: #6366f1;
  background: #fff;
  box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1);
}

.search-row {
  display: flex;
  gap: 14px;
}

.search-row input {
  padding-left: 44px;
}

.btn-search {
  padding: 14px 28px;
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
  color: #fff;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  transition: all 0.2s ease;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.35);
}

.btn-search:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(99, 102, 241, 0.45);
}

.btn-search svg {
  width: 20px;
  height: 20px;
}

/* 加载状态 */
.loading {
  text-align: center;
  padding: 40px 20px;
}

.loading-dots {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-bottom: 12px;
}

.loading-dots span {
  width: 10px;
  height: 10px;
  background: #6366f1;
  border-radius: 50%;
  animation: bounce 0.6s ease infinite;
}

.loading-dots span:nth-child(2) { animation-delay: 0.1s; }
.loading-dots span:nth-child(3) { animation-delay: 0.2s; }

.loading p {
  color: #64748b;
  font-size: 14px;
  margin: 0;
}

/* 错误 */
.error {
  display: flex;
  align-items: center;
  gap: 10px;
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
  color: #dc2626;
  padding: 14px 18px;
  border-radius: 12px;
  margin-bottom: 20px;
  font-size: 14px;
  border: 1px solid #fecaca;
}

.error svg {
  width: 20px;
  height: 20px;
}

/* 结果区域 */
.result-section {
  margin-top: 24px;
}

.result-header {
  margin-bottom: 16px;
}

.result-count {
  font-size: 14px;
  color: #475569;
}

.result-count strong {
  color: #6366f1;
  font-weight: 700;
}

.result-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 18px;
}

.result-card {
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  padding: 18px;
  cursor: pointer;
  background: #fff;
  transition: all 0.25s ease;
  animation: fadeInUp 0.5s ease forwards;
  opacity: 0;
}

.result-card:hover {
  border-color: #c7d2fe;
  box-shadow: 0 8px 24px rgba(99, 102, 241, 0.12);
  transform: translateY(-4px);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.badge {
  display: inline-block;
  background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%);
  color: #4f46e5;
  padding: 5px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}

.sub-badge {
  display: inline-block;
  background: #f1f5f9;
  color: #64748b;
  padding: 5px 10px;
  border-radius: 6px;
  font-size: 11px;
}

.result-card h4 {
  margin: 0 0 10px;
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  line-height: 1.45;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.result-card p {
  margin: 0;
  font-size: 13px;
  color: #64748b;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 12px;
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 12px;
  border-top: 1px solid #f1f5f9;
}

.news-id {
  font-family: 'SF Mono', monospace;
  font-size: 12px;
  color: #94a3b8;
}

.view-text {
  font-size: 12px;
  color: #6366f1;
  font-weight: 500;
  opacity: 0;
  transform: translateX(-5px);
  transition: all 0.2s ease;
}

.result-card:hover .view-text {
  opacity: 1;
  transform: translateX(0);
}

/* 空状态 */
.empty-tip {
  text-align: center;
  padding: 60px 20px;
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

.empty-tip h3 {
  margin: 0 0 10px;
  font-size: 1.1rem;
  font-weight: 600;
  color: #475569;
}

.empty-tip p {
  margin: 0;
  color: #94a3b8;
  font-size: 14px;
}

@media (max-width: 768px) {
  .search-row {
    flex-direction: column;
  }
  
  .result-grid {
    grid-template-columns: 1fr;
  }
}
</style>
