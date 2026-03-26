<template>
  <main class="recommend-main">
    <div class="content-wrap">
      <!-- 加载状态 -->
      <div v-if="loading" class="loading-container">
        <div class="loading-spinner">
          <div class="spinner-ring"></div>
          <div class="spinner-ring"></div>
          <div class="spinner-ring"></div>
        </div>
        <p>正在为您精选内容...</p>
      </div>
      
      <!-- 错误提示 -->
      <div v-if="error" class="error animate-shake">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        {{ error }}
      </div>
      
      <!-- 推荐内容 -->
      <div v-if="recommendations.length > 0" class="recommendations">
        <div class="recommend-header">
          <div class="header-content">
            <div class="header-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                <path d="M2 17l10 5 10-5"/>
                <path d="M2 12l10 5 10-5"/>
              </svg>
            </div>
            <div class="header-text">
              <h2>推荐</h2>
              
            </div>
          </div>
          <button type="button" class="btn-refresh" @click="$emit('refresh')">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 12a9 9 0 11-9-9"/>
              <polyline points="21,3 21,9 15,9"/>
            </svg>
            换一批
          </button>
        </div>
        
        <div class="news-grid">
          <NewsCard
            v-for="(news, index) in recommendations"
            :key="news.id"
            :news="news"
            :style="{ animationDelay: `${index * 0.1}s` }"
            class="news-card-animate"
            @click="$emit('open-detail', $event)"
            @like="$emit('like', $event)"
            @dislike="$emit('dislike', $event)"
            @favorite="$emit('favorite', $event)"
            @not-interested="$emit('not-interested', $event)"
          />
        </div>
      </div>
      
      <!-- 空状态 -->
      <div v-else-if="!loading" class="empty-tip">
        <div class="empty-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1"/>
            <path d="M2 12h10"/>
            <path d="M2 16h10"/>
            <path d="M2 20h10"/>
            <circle cx="17" cy="16" r="3"/>
            <path d="M19 17c1.5 1.5 3 2.5 3 5 0 2.5-2 4-4 4h-2"/>
          </svg>
        </div>
        <h3>暂无推荐内容</h3>
        <p>多浏览一些新闻，我们就能更好地了解您的兴趣</p>
        <button class="btn-start" @click="$emit('refresh')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 12a9 9 0 11-9-9"/>
            <polyline points="21,3 21,9 15,9"/>
          </svg>
          重新加载
        </button>
      </div>
    </div>
  </main>
</template>

<script>
import NewsCard from './NewsCard.vue'

export default {
  name: 'RecommendView',
  components: { NewsCard },
  props: {
    recommendations: { type: Array, default: () => [] },
    loading: { type: Boolean, default: false },
    error: { type: String, default: '' }
  },
  emits: ['refresh', 'open-detail', 'like', 'dislike', 'favorite', 'not-interested']
}
</script>

<style scoped>
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-5px); }
  75% { transform: translateX(5px); }
}

@keyframes pulse-ring {
  0% {
    transform: scale(0.8);
    opacity: 0.8;
  }
  100% {
    transform: scale(1.4);
    opacity: 0;
  }
}

.recommend-main .content-wrap {
  max-width: 1200px;
  margin: 0 auto;
  box-sizing: border-box;
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
  width: 60px;
  height: 60px;
  margin-bottom: 20px;
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
  width: 80%;
  height: 80%;
  top: 10%;
  left: 10%;
  border-top-color: #8b5cf6;
  animation-duration: 1s;
  animation-direction: reverse;
}

.spinner-ring:nth-child(3) {
  width: 60%;
  height: 60%;
  top: 20%;
  left: 20%;
  border-top-color: #a78bfa;
  animation-duration: 0.8s;
}

.loading-container p {
  color: #64748b;
  font-size: 15px;
  margin: 0;
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
  margin-bottom: 20px;
  font-size: 14px;
  border: 1px solid #fecaca;
}

.error svg {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.animate-shake {
  animation: shake 0.4s ease;
}

/* 推荐头部 */
.recommend-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 16px;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 14px;
}

.header-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 6px 16px rgba(99, 102, 241, 0.35);
}

.header-icon svg {
  width: 24px;
  height: 24px;
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

/* 刷新按钮 */
.btn-refresh {
  padding: 10px 18px;
  font-size: 14px;
  color: #6366f1;
  background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%);
  border: 1px solid #c7d2fe;
  border-radius: 10px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  transition: all 0.2s ease;
}

.btn-refresh svg {
  width: 16px;
  height: 16px;
  transition: transform 0.3s ease;
}

.btn-refresh:hover {
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
  color: #fff;
  border-color: transparent;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.35);
}

.btn-refresh:hover svg {
  transform: rotate(180deg);
}

/* 新闻网格 */
.news-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.news-card-animate {
  animation: fadeInUp 0.5s ease forwards;
  opacity: 0;
}

/* 空状态 */
.empty-tip {
  text-align: center;
  padding: 80px 20px;
}

.empty-icon {
  width: 90px;
  height: 90px;
  margin: 0 auto 24px;
  background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.empty-icon::before {
  content: '';
  position: absolute;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  border: 2px solid #6366f1;
  animation: pulse-ring 2s ease-out infinite;
}

.empty-icon svg {
  width: 45px;
  height: 45px;
  color: #94a3b8;
  position: relative;
  z-index: 1;
}

.empty-tip h3 {
  margin: 0 0 10px;
  font-size: 1.25rem;
  font-weight: 600;
  color: #475569;
}

.empty-tip p {
  margin: 0 0 24px;
  color: #94a3b8;
  font-size: 14px;
}

.btn-start {
  padding: 12px 24px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: #fff;
  border: none;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s ease;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.35);
}

.btn-start:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(99, 102, 241, 0.45);
}

.btn-start svg {
  width: 18px;
  height: 18px;
}

@media (max-width: 768px) {
  .news-grid {
    grid-template-columns: 1fr;
  }
  
  .recommend-header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
