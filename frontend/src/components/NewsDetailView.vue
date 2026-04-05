<template>
  <main class="detail-main">
    <div class="detail-container">
      <button type="button" class="btn-back" @click="$emit('back')">← 返回推荐</button>
      <article v-if="news" class="detail-article">
        <div class="detail-tags">
          <span class="detail-category">{{ news.category }}</span>
          <span v-if="news.subcategory" class="detail-subcategory">{{ news.subcategory }}</span>
        </div>
        <h1 class="detail-title">{{ news.title }}</h1>
        <p v-if="news.abstract" class="detail-abstract">{{ news.abstract }}</p>
        <pre v-if="news.body" class="detail-body">{{ news.body }}</pre>
        <p v-else class="detail-no-body">暂无正文 (body: {{ news.body }})</p>
        
        <div class="detail-actions">
          <button
            type="button"
            class="btn-like"
            :class="{ liked: userLiked }"
            @click="toggleLike"
            :disabled="likeLoading"
          >
            <span class="like-icon">{{ userLiked ? '👍' : '👍' }}</span>
            <span class="like-count">{{ likeCount }}</span>
          </button>
        </div>
        
        <p class="detail-id">ID: {{ news.id }}</p>
      </article>
    </div>
  </main>
</template>

<script>
import { api } from '../api.js'

export default {
  name: 'NewsDetailView',
  props: {
    news: { type: Object, default: null },
    userId: { type: String, default: '' }
  },
  emits: ['back', 'like', 'unlike'],
  data() {
    return {
      likeCount: 0,
      userLiked: false,
      likeLoading: false
    }
  },
  watch: {
    news: {
      immediate: true,
      handler(newVal) {
        if (newVal) {
          this.likeCount = newVal.like_count || 0
          this.userLiked = newVal.user_liked || false
        }
      }
    }
  },
  methods: {
    async toggleLike() {
      if (!this.userId || this.likeLoading) return
      
      this.likeLoading = true
      try {
        if (this.userLiked) {
          // 取消点赞：发送 dislike 事件
          await api.postEvent({
            user_id: this.userId,
            news_id: this.news.id,
            event_type: 'dislike'
          })
          this.likeCount = Math.max(0, this.likeCount - 1)
          this.userLiked = false
          this.$emit('unlike', this.news.id)
        } else {
          // 点赞
          await api.postEvent({
            user_id: this.userId,
            news_id: this.news.id,
            event_type: 'like'
          })
          this.likeCount += 1
          this.userLiked = true
          this.$emit('like', this.news.id)
        }
      } catch (err) {
        console.error('点赞操作失败:', err)
      } finally {
        this.likeLoading = false
      }
    }
  }
}
</script>

<style scoped>
.detail-main {
  padding: 24px 20px;
  max-width: 800px;
  margin: 0 auto;
  box-sizing: border-box;
}

.detail-container {
  background: #fff;
  padding: 28px 32px;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  border: 1px solid #e2e8f0;
}

.btn-back {
  padding: 8px 16px;
  margin-bottom: 20px;
  font-size: 14px;
  color: #0d9488;
  background: transparent;
  border: 1px solid #0d9488;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
}

.btn-back:hover {
  background: #ccfbf1;
  color: #0f766e;
}

.detail-tags {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.detail-category {
  display: inline-block;
  background: #ccfbf1;
  color: #0f766e;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
}

.detail-subcategory {
  display: inline-block;
  background: #e0e7ff;
  color: #4338ca;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
}

.detail-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #1e293b;
  line-height: 1.4;
  margin-bottom: 32px;
}

.detail-abstract {
  font-size: 1.25rem;
  color: #000;
  line-height: 1.4;
  white-space: pre-wrap;
  margin-bottom: 20px;
}

.detail-body {
  font-size: 1.25rem;
  color: #000;
  line-height: 1.6;
  white-space: pre-wrap;
  margin-bottom: 20px;
}

.detail-no-body {
  font-size: 0.875rem;
  color: #999;
  margin-bottom: 20px;
}

.detail-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 16px;
  margin-bottom: 16px;
  padding: 16px 0;
  border-top: 1px solid #e2e8f0;
  border-bottom: 1px solid #e2e8f0;
}

.btn-like {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  font-size: 14px;
  color: #64748b;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-like:hover:not(:disabled) {
  background: #fee2e2;
  border-color: #fca5a5;
  color: #dc2626;
}

.btn-like.liked {
  background: #fee2e2;
  border-color: #fca5a5;
  color: #dc2626;
}

.btn-like:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.like-icon {
  font-size: 16px;
}

.like-count {
  font-weight: 600;
  min-width: 20px;
  text-align: center;
}

.detail-id {
  margin-top: 16px;
  font-size: 12px;
  color: #94a3b8;
}
</style>
