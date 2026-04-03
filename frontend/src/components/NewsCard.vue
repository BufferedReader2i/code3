<template>
  <div class="news-card" @click="$emit('click', news)">
    <div class="news-header">
      <span class="category">{{ news.category }}</span>
    </div>
    <h3>{{ news.title }}</h3>
    <p v-if="news.abstract">{{ news.abstract }}</p>
    <div class="news-footer">
      <span class="id">ID: {{ news.id }}</span>
      <div class="actions" @click.stop>
        <button type="button" class="btn-act like" :class="{ done: feedback.like }" @click="onLike"> {{ feedback.like ? '已赞' : '赞' }} </button>
        <button type="button" class="btn-act dislike" :class="{ done: feedback.dislike }" @click="onDislike"> {{ feedback.dislike ? '已踩' : '踩' }} </button>
        <button type="button" class="btn-act fav" :class="{ done: feedback.fav }" @click="onFav"> {{ feedback.fav ? '已收藏' : '收藏' }} </button>
        <button type="button" class="btn-act ni" :class="{ done: feedback.ni }" @click="onNi"> {{ feedback.ni ? '已标记' : '不感兴趣' }} </button>
      </div>
    </div>
  </div>
</template>

<script>
import { reactive } from 'vue'

export default {
  name: 'NewsCard',
  props: {
    news: { type: Object, required: true }
  },
  emits: ['click', 'like', 'unlike', 'dislike', 'undislike', 'favorite', 'unfavorite', 'not-interested', 'remove-not-interested'],
  setup(props, { emit }) {
    const feedback = reactive({ like: false, dislike: false, fav: false, ni: false })
    
    function onLike() {
      if (feedback.like) {
        feedback.like = false
        emit('unlike', props.news)
      } else {
        feedback.like = true
        emit('like', props.news)
      }
    }
    
    function onDislike() {
      if (feedback.dislike) {
        feedback.dislike = false
        emit('undislike', props.news)
      } else {
        feedback.dislike = true
        emit('dislike', props.news)
      }
    }
    
    function onFav() {
      if (feedback.fav) {
        feedback.fav = false
        emit('unfavorite', props.news)
      } else {
        feedback.fav = true
        emit('favorite', props.news)
      }
    }
    
    function onNi() {
      if (feedback.ni) {
        feedback.ni = false
        emit('remove-not-interested', props.news)
      } else {
        feedback.ni = true
        emit('not-interested', props.news)
      }
    }
    
    return { feedback, onLike, onDislike, onFav, onNi }
  }
}
</script>

<style scoped>
.news-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 2px rgba(0,0,0,0.04);
  cursor: pointer;
  transition: box-shadow 0.2s, border-color 0.2s, transform 0.2s;
}

.news-card:hover {
  border-color: #93c5fd;
  box-shadow: 0 4px 12px rgba(37,99,235,0.2);
  transform: translateY(-2px);
}

.news-header { margin-bottom: 10px; }

.category {
  display: inline-block;
  background: #dbeafe;
  color: #1d4ed8;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
}

.news-card h3 {
  font-size: 15px;
  font-weight: 600;
  line-height: 1.45;
  color: #1e293b;
  margin-bottom: 8px;
}

.news-card p {
  font-size: 13px;
  color: #64748b;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.news-reason {
  margin-top: 10px;
  padding: 8px 12px;
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  border-radius: 8px;
  font-size: 12px;
  color: #92400e;
  display: flex;
  align-items: center;
  gap: 6px;
}

.news-reason .reason-icon {
  font-size: 14px;
}

.news-reason .reason-text {
  flex: 1;
  line-height: 1.4;
}

.news-footer {
  margin-top: 12px;
  font-size: 12px;
  color: #94a3b8;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.actions {
  display: inline-flex;
  gap: 6px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.btn-act {
  border: 1px solid #e2e8f0;
  background: #fff;
  color: #475569;
  padding: 4px 8px;
  border-radius: 8px;
  font-size: 12px;
  cursor: pointer;
}

.btn-act:hover { background: #f8fafc; }
.btn-act.like { border-color: #86efac; color: #166534; }
.btn-act.dislike { border-color: #fca5a5; color: #991b1b; }
.btn-act.fav { border-color: #93c5fd; color: #1d4ed8; }
.btn-act.ni { border-color: #cbd5e1; color: #334155; }
.btn-act.done { font-weight: 700; opacity: 1; }
.btn-act.like.done { background: #dcfce7; border-color: #22c55e; color: #166534; }
.btn-act.dislike.done { background: #fee2e2; border-color: #ef4444; color: #991b1b; }
.btn-act.fav.done { background: #dbeafe; border-color: #3b82f6; color: #1d4ed8; }
.btn-act.ni.done { background: #f1f5f9; border-color: #64748b; color: #334155; }
</style>
