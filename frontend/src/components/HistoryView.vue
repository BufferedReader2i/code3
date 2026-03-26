<template>
  <main class="history-page">
    <div class="history-container">
      <!-- 标题区域 -->
      <div class="history-header">
        <div class="header-content">
          <div class="header-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <polyline points="12,6 12,12 16,14"/>
            </svg>
          </div>
          <div class="header-text">
            <h2>历史浏览</h2>
            
          </div>
        </div>
        <div v-if="historyCount !== null" class="history-count-badge">
          <span class="count-number">{{ historyCount }}</span>
          <span class="count-label">条记录</span>
        </div>
      </div>

      

      <!-- 加载状态 -->
      <div v-if="historyLoading" class="loading-container">
        <div class="loading-pulse">
          <div class="pulse-ring"></div>
          <div class="pulse-ring"></div>
          <div class="pulse-ring"></div>
        </div>
        <p>正在加载浏览历史...</p>
      </div>

      <!-- 历史列表 -->
      <div v-else-if="historyList.length" class="history-list">
        <div
          v-for="(item, index) in historyList"
          :key="item.id"
          class="history-item"
          :style="{ animationDelay: `${index * 0.05}s` }"
          @click="$emit('open-detail', item)"
        >
         
          <div class="item-content">
            <div class="item-header">
              <span class="history-cat">{{ item.category }}</span>
              <span v-if="item.subcategory" class="sub-badge">{{ item.subcategory }}</span>
            </div>
            <h4>{{ item.title }}</h4>
            <p v-if="item.abstract">{{ item.abstract }}</p>
          </div>
          <div class="item-arrow">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M5 12h14"/>
              <path d="m12 5 7 7-7 7"/>
            </svg>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else class="empty-tip">
        <div class="empty-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
            <circle cx="12" cy="12" r="3"/>
          </svg>
        </div>
        <h3>暂无浏览历史</h3>
        
      </div>
    </div>
  </main>
</template>

<script>
export default {
  name: 'HistoryView',
  props: {
    historyList: { type: Array, default: () => [] },
    historyLoading: { type: Boolean, default: false },
    historyCount: { type: Number, default: null }
  }
}
</script>

<style scoped>
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes pulse {
  0%, 100% { opacity: 0.3; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(1.1); }
}

.history-page { 
  max-width: 1200px; 
  margin: 0 auto; 
  box-sizing: border-box; 
}

.history-container {
  background: #fff;
  padding: 32px;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  border: 1px solid #e2e8f0;
}

/* 标题 */
.history-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  flex-wrap: wrap;
  gap: 16px;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon {
  width: 52px;
  height: 52px;
  background: linear-gradient(135deg, #0d9488 0%, #14b8a6 100%);
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 6px 16px rgba(13, 148, 136, 0.35);
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

/* 计数徽章 */
.history-count-badge {
  display: flex;
  align-items: baseline;
  gap: 6px;
  padding: 10px 18px;
  background: linear-gradient(135deg, #e0f2f1 0%, #ccfbf1 100%);
  border-radius: 25px;
  border: 1px solid #99f6e4;
}

.count-number {
  font-size: 24px;
  font-weight: 700;
  color: #0d9488;
  font-family: 'Inter', system-ui, sans-serif;
}

.count-label {
  font-size: 13px;
  color: #0d9488;
}

/* 提示 */
.hint {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #64748b;
  margin-bottom: 20px;
  padding: 12px 16px;
  background: #f8fafc;
  border-radius: 10px;
}

.hint svg {
  width: 16px;
  height: 16px;
  color: #94a3b8;
}

/* 加载状态 */
.loading-container {
  text-align: center;
  padding: 60px 20px;
}

.loading-pulse {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-bottom: 16px;
}

.pulse-ring {
  width: 12px;
  height: 12px;
  background: #0d9488;
  border-radius: 50%;
  animation: pulse 1s ease infinite;
}

.pulse-ring:nth-child(2) { animation-delay: 0.15s; }
.pulse-ring:nth-child(3) { animation-delay: 0.3s; }

.loading-container p {
  color: #64748b;
  font-size: 14px;
  margin: 0;
}

/* 历史列表 */
.history-list { 
  margin-top: 8px; 
}

.history-item {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 20px;
  border-radius: 14px;
  margin-bottom: 12px;
  background: #fff;
  border: 1px solid #f1f5f9;
  transition: all 0.25s ease;
  animation: fadeInUp 0.4s ease forwards;
  opacity: 0;
}

.history-item:hover {
  border-color: #99f6e4;
  background: linear-gradient(135deg, #f0fdfa 0%, #fff 100%);
  transform: translateX(4px);
  box-shadow: 0 4px 12px rgba(13, 148, 136, 0.1);
}

.item-time {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #e0f2f1 0%, #ccfbf1 100%);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.item-time svg {
  width: 20px;
  height: 20px;
  color: #0d9488;
}

.item-content {
  flex: 1;
  min-width: 0;
}

.item-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.history-cat {
  display: inline-block;
  background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%);
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

.history-item h4 {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 6px;
  line-height: 1.45;
}

.history-item p { 
  font-size: 13px; 
  color: #64748b; 
  line-height: 1.5;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.item-arrow {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transform: translateX(-10px);
  transition: all 0.2s ease;
}

.item-arrow svg {
  width: 20px;
  height: 20px;
  color: #0d9488;
}

.history-item:hover .item-arrow {
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

@media (max-width: 640px) {
  .history-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .history-item {
    flex-direction: column;
    gap: 12px;
  }
  
  .item-arrow {
    display: none;
  }
}
</style>
