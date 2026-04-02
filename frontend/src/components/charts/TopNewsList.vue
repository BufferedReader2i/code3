<template>
  <div class="top-news-list">
    <div class="list-header">{{ title }}</div>
    <div class="list-body">
      <div 
        v-for="(item, index) in displayList" 
        :key="index"
        class="list-item"
        :style="{ backgroundColor: getCategoryBgColor(item.category) }"
      >
        <span class="rank">{{ index + 1 }}</span>
        <span 
          class="category-tag" 
          :style="{ backgroundColor: getCategoryColor(item.category) }"
        >
          {{ item.category || 'N/A' }}
        </span>
        <span class="news-title">{{ item[nameKey] }}</span>
        <span class="news-count">{{ item[valueKey] }}</span>
      </div>
      <div v-if="!displayList.length" class="empty-state">
        暂无数据
      </div>
    </div>
  </div>
</template>

<script>
// 与 PieChart 使用相同的颜色方案
const COLORS = [
  '#6366f1', '#8b5cf6', '#ec4899', '#f43f5e', '#f59e0b',
  '#10b981', '#06b6d4', '#3b82f6', '#14b8a6', '#a855f7'
]

// 淡色背景版本
const BG_COLORS = [
  'rgba(99, 102, 241, 0.08)', 'rgba(139, 92, 246, 0.08)', 'rgba(236, 72, 153, 0.08)', 
  'rgba(244, 63, 94, 0.08)', 'rgba(245, 158, 11, 0.08)', 'rgba(16, 185, 129, 0.08)', 
  'rgba(6, 182, 212, 0.08)', 'rgba(59, 130, 246, 0.08)', 'rgba(20, 184, 166, 0.08)', 
  'rgba(168, 85, 247, 0.08)'
]

export default {
  name: 'TopNewsList',
  props: {
    data: { type: Array, default: () => [] },
    title: { type: String, default: '' },
    nameKey: { type: String, default: 'title' },
    valueKey: { type: String, default: 'count' },
    categories: { type: Array, default: () => [] }
  },
  computed: {
    displayList() {
      return this.data.slice(0, 10)
    },
    categoryColorMap() {
      const map = {}
      this.categories.forEach((cat, i) => {
        map[cat.name] = { color: COLORS[i % COLORS.length], bg: BG_COLORS[i % BG_COLORS.length] }
      })
      return map
    }
  },
  methods: {
    getCategoryColor(category) {
      if (!category) return '#94a3b8'
      return this.categoryColorMap[category]?.color || COLORS[Object.keys(this.categoryColorMap).indexOf(category) % COLORS.length] || '#94a3b8'
    },
    getCategoryBgColor(category) {
      if (!category) return 'rgba(148, 163, 184, 0.08)'
      return this.categoryColorMap[category]?.bg || BG_COLORS[Object.keys(this.categoryColorMap).indexOf(category) % BG_COLORS.length] || 'rgba(148, 163, 184, 0.08)'
    }
  }
}
</script>

<style scoped>
.top-news-list {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fff;
}

.list-header {
  text-align: center;
  padding: 18px 16px 14px;
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
  font-family: 'Inter', system-ui, sans-serif;
  border-bottom: 1px solid #f1f5f9;
}

.list-body {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.list-item {
  display: flex;
  align-items: center;
  padding: 12px 14px;
  border-radius: 10px;
  transition: all 0.2s ease;
  gap: 12px;
  margin-bottom: 4px;
}

.list-item:hover {
  transform: translateX(4px);
  filter: brightness(0.96);
}

.rank {
  min-width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  color: #64748b;
  background: #fff;
  border-radius: 6px;
  flex-shrink: 0;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.category-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 48px;
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  color: #fff;
  flex-shrink: 0;
  letter-spacing: 0.3px;
}

.news-title {
  flex: 1;
  font-size: 14px;
  color: #334155;
  line-height: 1.5;
  word-break: break-all;
  font-weight: 500;
}

.news-count {
  font-size: 14px;
  font-weight: 700;
  color: #334155;
  white-space: nowrap;
  flex-shrink: 0;
  padding: 4px 10px;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 8px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #94a3b8;
  font-size: 14px;
}
</style>
