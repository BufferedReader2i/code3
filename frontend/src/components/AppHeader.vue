<template>
  <header class="main-header">
    <!-- Logo 区域 -->
    <div class="header-logo">
      <!-- <div class="logo-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1"/>
          <path d="M2 12h10"/>
          <path d="M2 16h10"/>
          <path d="M2 20h10"/>
          <circle cx="17" cy="16" r="3"/>
          <path d="M19 17c1.5 1.5 3 2.5 3 5 0 2.5-2 4-4 4h-2"/>
        </svg>
      </div> -->
      <h1 class="header-title">新闻推荐系统</h1>
    </div>

    <template v-if="token">
      <nav class="header-tabs">
        <button type="button" class="nav-tab" :class="{ active: currentPage === 'recommend' || currentPage === 'detail' }" @click="$emit('navigate', 'recommend')">
          <span>新闻推荐</span>
        </button>
        <button type="button" class="nav-tab" :class="{ active: currentPage === 'search' }" @click="$emit('navigate', 'search')">
          <span>搜索发现</span>
        </button>
        <!-- <button type="button" class="nav-tab" :class="{ active: currentPage === 'chat-recommend' }" @click="$emit('navigate', 'chat-recommend')">
          <span>智能对话</span>
        </button> -->
        <button type="button" class="nav-tab" :class="{ active: currentPage === 'profile' }" @click="$emit('navigate', 'profile')">
          <span>个人中心</span>
        </button>
        <button type="button" class="nav-tab" :class="{ active: currentPage === 'history' }" @click="$emit('navigate', 'history')">
          <span>历史浏览</span>
        </button>
        <button type="button" class="nav-tab" :class="{ active: currentPage === 'favorites' }" @click="$emit('navigate', 'favorites')">
          <span>我的收藏</span>
        </button>
        <button v-if="isAdmin" type="button" class="nav-tab" :class="{ active: currentPage === 'upload' }" @click="$emit('navigate', 'upload')">
          <span>新闻发布</span>
        </button>
        <button v-if="isAdmin" type="button" class="nav-tab" :class="{ active: currentPage === 'news-management' }" @click="$emit('navigate', 'news-management')">
          <span>新闻管理</span>
        </button>
        <button v-if="isAdmin" type="button" class="nav-tab" :class="{ active: currentPage === 'admin' }" @click="$emit('navigate', 'admin')">
          <span>数据后台</span>
        </button>
      </nav>
      <div class="header-right">
        <div class="user-info">
          <div class="user-avatar">{{ currentUser.username?.charAt(0).toUpperCase() }}</div>
          <span class="header-username">{{ currentUser.username }}</span>
          <button type="button" class="btn-settings" @click="$emit('navigate', 'change-password')" title="修改密码">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="3"/>
              <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z"/>
            </svg>
          </button>
        </div>
        <button type="button" class="btn-logout" @click="$emit('logout')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/>
            <polyline points="16,17 21,12 16,7"/>
            <line x1="21" y1="12" x2="9" y2="12"/>
          </svg>
          <span>退出</span>
        </button>
      </div>
    </template>
  </header>
</template>

<script>
export default {
  name: 'AppHeader',
  props: {
    currentPage: { type: String, default: 'recommend' },
    token: { type: String, default: '' },
    currentUser: { type: Object, default: () => ({ username: '', role: 'user' }) }
  },
  emits: ['navigate', 'logout'],
  computed: {
    isAdmin() {
      return this.currentUser?.role === 'admin'
    }
  }
}
</script>

<style scoped>
/* 顶栏容器 */
.main-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  background-color: #1a3a5c;
  color: #ffffff;
  padding: 0 24px;
  min-height: 64px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.2);
  position: relative;
}

/* Logo 区域 */
.header-logo {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.logo-icon {
  width: 40px;
  height: 40px;
  background-color: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-icon svg {
  width: 22px;
  height: 22px;
  color: #ffffff;
}

.header-title {
  font-size: 1.15rem;
  font-weight: 600;
  margin: 0;
  color: #ffffff;
  letter-spacing: 0.02em;
}

/* 导航标签 */
.header-tabs {
  display: flex;
  align-items: center;
  flex: 1;
  justify-content: center;
  gap: 4px;
}

.nav-tab {
  padding: 0 16px;
  font-size: 14px;
  font-weight: 500;
  letter-spacing: 0.01em;
  border: none;
  background: transparent;
  color: rgba(255, 255, 255, 0.7);
  cursor: pointer;
  transition: all 0.2s ease;
  min-height: 56px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  position: relative;
  border-radius: 4px;
}

.nav-tab span {
  position: relative;
}

.nav-tab:hover {
  background-color: rgba(255, 255, 255, 0.1);
  color: #ffffff;
  border-radius: 4px;
}

.nav-tab.active {
  color: #ffffff;
  font-weight: 600;
}

.nav-tab.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  height: 2px;
  background-color: #ffffff;
  border-radius: 2px;
}

/* 右侧用户区域 */
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 12px 6px 6px;
  background-color: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.2s ease;
}

.user-info:hover {
  background-color: rgba(255, 255, 255, 0.15);
}

.user-avatar {
  width: 32px;
  height: 32px;
  background-color: #4a7ab5;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
  color: #ffffff;
}

.header-username {
  font-size: 14px;
  color: #ffffff;
  font-weight: 500;
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.btn-settings {
  padding: 4px;
  background: transparent;
  border: none;
  cursor: pointer;
  color: rgba(255, 255, 255, 0.7);
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  margin-left: 4px;
}

.btn-settings svg {
  width: 16px;
  height: 16px;
}

.btn-settings:hover {
  color: #ffffff;
  background-color: rgba(255, 255, 255, 0.1);
}

.btn-logout {
  padding: 8px 16px;
  font-size: 13px;
  font-weight: 500;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 4px;
  background: transparent;
  color: rgba(255, 255, 255, 0.9);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s ease;
}

.btn-logout svg {
  width: 14px;
  height: 14px;
}

.btn-logout:hover {
  background-color: rgba(239, 68, 68, 0.2);
  border-color: rgba(255, 255, 255, 0.4);
  color: #ffffff;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .nav-tab {
    padding: 0 12px;
    font-size: 13px;
  }

  .header-username {
    max-width: 80px;
  }
}

@media (max-width: 768px) {
  .main-header {
    padding: 0 16px;
    min-height: 56px;
  }

  .header-title {
    font-size: 1rem;
  }

  .logo-icon {
    width: 36px;
    height: 36px;
  }

  .logo-icon svg {
    width: 20px;
    height: 20px;
  }

  .nav-tab {
    padding: 0 10px;
    font-size: 12px;
    min-height: 48px;
  }

  .nav-tab.active::after {
    height: 2px;
  }

  .user-info {
    padding: 4px 8px 4px 4px;
  }

  .user-avatar {
    width: 28px;
    height: 28px;
    font-size: 12px;
  }

  .btn-logout span {
    display: none;
  }

  .btn-logout {
    padding: 8px;
  }

  .btn-logout svg {
    width: 16px;
    height: 16px;
  }
}
</style>
