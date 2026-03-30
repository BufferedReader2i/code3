<template>
  <main class="favorites-page">
    <div class="favorites-container">
      <div class="title-row">
        <div class="title-group">
          <div class="title-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
            </svg>
          </div>
          <h2>我的收藏</h2>
        </div>
        
      </div>

      <div v-if="error" class="error">{{ error }}</div>

      <div v-if="loading" class="loading">加载中...</div>

      <div v-else-if="favorites.length === 0" class="empty-state">
        <p>暂无收藏新闻</p>
      </div>

      <div v-else class="favorites-list">
        <div v-for="news in favorites" :key="news.id" class="favorite-item">
          <div class="news-content" @click="$emit('open-detail', news)">
            <div class="news-title">{{ news.title }}</div>
            <div class="news-meta">
              <span class="category">{{ news.category }}</span>
              
            </div>
            <div class="news-abstract">{{ news.abstract }}</div>
          </div>
          <button class="btn-remove" @click.stop="unfavorite(news)" title="取消收藏">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  </main>
</template>

<script>
import { apiCall } from '../api.js'

export default {
  name: 'FavoritesView',
  props: {
    userId: { type: String, default: '' }
  },
  emits: ['open-detail'],
  data() {
    return {
      favorites: [],
      loading: false,
      error: ''
    }
  },
  mounted() {
    this.loadFavorites()
  },
  methods: {
    async loadFavorites() {
      this.loading = true
      this.error = ''
      try {
        const res = await apiCall(`http://localhost:8000/api/user/favorites?user_id=${this.userId}&limit=100`, 'GET')
        this.favorites = res.items || []
      } catch (err) {
        this.error = err.message || '加载失败'
      } finally {
        this.loading = false
      }
    },
    async unfavorite(news) {
      try {
        await apiCall(`http://localhost:8000/api/event`, 'POST', {
          user_id: this.userId,
          news_id: news.id,
          event_type: 'unfavorite'
        })
        // 从列表中移除
        this.favorites = this.favorites.filter(f => f.id !== news.id)
      } catch (err) {
        this.error = err.message || '取消收藏失败'
      }
    }
  }
}
</script>

<style scoped>
.favorites-page {
  max-width: 1200px; 
  margin: 0 auto; 
  box-sizing: border-box; 
}

.favorites-container {

  background: #fff;
  padding: 32px;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  border: 1px solid #e2e8f0;
}

.title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.title-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-icon {
  width: 32px;
  height: 32px;
  color: #e91e63;
}

.title-icon svg {
  width: 100%;
  height: 100%;
}

.title-group h2 {
  font-size: 24px;
  color: #1a3a5c;
  margin: 0;
}

.btn-secondary {
  padding: 8px 16px;
  background: #f0f0f0;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.btn-secondary:hover {
  background: #e0e0e0;
}

.btn-secondary svg {
  width: 16px;
  height: 16px;
}

.error {
  padding: 12px;
  background: #fee;
  color: #c33;
  border-radius: 4px;
  margin-bottom: 16px;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #666;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #999;
}

.favorites-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.favorite-item {
  background: white;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.favorite-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.news-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.news-title {
  font-size: 16px;
  font-weight: 600;
  color: #1a3a5c;
}

.news-meta {
  display: flex;
  gap: 8px;
  font-size: 12px;
}

.category, .subcategory {
  background: #f0f0f0;
  padding: 4px 8px;
  border-radius: 4px;
  color: #666;
}

.news-abstract {
  color: #666;
  font-size: 14px;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.btn-remove {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border: 1px solid #e2e8f0;
  background: #fff;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
  transition: all 0.2s;
}

.btn-remove:hover {
  background: #fee2e2;
  border-color: #ef4444;
  color: #ef4444;
}

.btn-remove svg {
  width: 16px;
  height: 16px;
}
</style>
