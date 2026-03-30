<template>
  <main class="news-management-page">
    <div class="management-container">
      <div class="title-row">
        <div class="title-group">
          <div class="title-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
              <polyline points="14,2 14,8 20,8"/>
              <line x1="16" y1="13" x2="8" y2="13"/>
              <line x1="16" y1="17" x2="8" y2="17"/>
            </svg>
          </div>
          <h2>新闻管理</h2>
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

      <!-- 编辑对话框 -->
      <div v-if="showEditDialog" class="modal-overlay" @click="cancelEdit">
        <div class="modal-content" @click.stop>
          <div class="modal-header">
            <h3>编辑新闻</h3>
            <button type="button" class="modal-close" @click="cancelEdit">×</button>
          </div>
          <div class="modal-body">
            <div class="form-group">
              <label>标题</label>
              <input v-model="editingNews.title" type="text" class="form-input">
            </div>
            <div class="form-group">
              <label>摘要</label>
              <textarea v-model="editingNews.abstract" class="form-input" rows="3"></textarea>
            </div>
            <div class="form-group">
              <label>正文</label>
              <textarea v-model="editingNews.body" class="form-input" rows="4"></textarea>
            </div>
            <div class="form-group">
              <label>类别</label>
              <input v-model="editingNews.category" type="text" class="form-input">
            </div>
            <div class="form-group">
              <label>子类别</label>
              <input v-model="editingNews.subcategory" type="text" class="form-input">
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn-cancel" @click="cancelEdit">取消</button>
            <button type="button" class="btn-save" @click="saveEditNews">保存</button>
          </div>
        </div>
      </div>

      <!-- 需审核的新闻 -->
      <div v-if="flaggedNews.length" class="section-container">
        <div class="section-header">
          <h3>需审核的新闻</h3>
          <span class="count-badge">{{ flaggedNews.length }} 条</span>
        </div>
        <div class="flagged-news-list">
          <div v-for="(n, index) in flaggedNews" :key="n.news_id" class="flagged-news-item" :style="{ animationDelay: `${index * 0.05}s` }">
            <div class="item-header">
            
              <span class="status-badge" :class="n.status">{{ n.status === 'active' ? '已发布' : '下架' }}</span>
            </div>
            <h4 class="flagged-title">{{ n.title }}</h4>
            <p class="flagged-abstract">{{ n.abstract }}</p>
            <div class="item-actions">
              <button type="button" class="btn-mini btn-danger" @click="toggleStatus(n)">
                {{ n.status === 'active' ? '下架' : '上架' }}
              </button>
              <!-- <button type="button" class="btn-mini" @click="editNews(n)">修改</button> -->
              <button type="button" class="btn-mini btn-delete" @click="deleteNews(n)">删除</button>
            </div>
          </div>
        </div>
      </div>

      <!-- 常规新闻列表 -->
      <div class="section-container">
        <div class="section-header">
          <h3>新闻列表</h3>
          <div class="header-controls">
            <input v-model="searchQ" type="text" placeholder="搜索标题..." class="search-input">
            <select v-model="filterCategory" class="filter-select">
              <option value="">全部类别</option>
              <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
            </select>
            <select v-model="filterStatus" class="filter-select">
              <option value="">全部状态</option>
              <option value="active">已发布</option>
              <option value="inactive">下架</option>
            </select>
            <button type="button" class="btn-search" @click="doSearch">搜索</button>
          </div>
        </div>

        <div v-if="displayedNews.length" class="table-wrap">
          <table class="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>标题</th>
                <th>类别</th>
                <th>话题</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(n, index) in displayedNews" :key="n.news_id" :style="{ animationDelay: `${index * 0.05}s` }">
                <td class="mono">{{ n.news_id }}</td>
                <td class="title">{{ n.title }}</td>
                <td><span class="category-tag">{{ n.category }}</span></td>
                <td>{{ n.subcategory }}</td>
                <td>
                  <span class="pill" :class="n.status">
                    <span class="status-dot"></span>
                    {{ n.status === 'active' ? '已发布' : '下架' }}
                  </span>
                </td>
                <td>
                  <button type="button" class="btn-mini" :class="{ 'btn-danger': n.status === 'active' }" @click="toggleStatus(n)">
                    {{ n.status === 'active' ? '下架' : '上架' }}
                  </button>
                   <!-- <button type="button" class="btn-mini" @click="editNews(n)">修改</button> -->
                  <button type="button" class="btn-mini btn-delete" @click="deleteNews(n)">删除</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>


        <div v-if="!displayedNews.length" class="empty-state">暂无新闻</div>
      </div>
    </div>
  </main>
</template>

<script>
export default {
  data() {
    return {
      flaggedNews: [],
      newsItems: [],
      error: null,
      searchQ: '',
      filterCategory: '',
      filterStatus: '',
      categories: [],
      showEditDialog: false,
      editingNews: { title: '', abstract: '', body: '', category: '', subcategory: '' },
    };
  },
  computed: {
    filteredNews() {
      return this.newsItems.filter(n => {
        const matchTitle = !this.searchQ || n.title.includes(this.searchQ);
        const matchCategory = !this.filterCategory || n.category === this.filterCategory;
        const matchStatus = !this.filterStatus || n.status === this.filterStatus;
        return matchTitle && matchCategory && matchStatus;
      });
    },
    displayedNews() {
      return this.filteredNews;
    }
  },
  mounted() {
    // 先加载需审核的新闻，再加载新闻列表
    this.loadFlaggedNews();
    
    // 异步加载分类数据，不影响主流程
    this.loadCategories();
  },
  methods: {
    loadFlaggedNews() {
      this.$api.getFlaggedNews()
        .then(response => {
          this.flaggedNews = response.data.items || [];
          // 加载新闻列表
          return this.$api.adminListNews({ limit: 20 });
        })
        .then(response => {
          this.newsItems = response.data.items || [];
          this.error = null;
        })
        .catch(err => {
          this.error = err.message || '加载新闻失败';
          console.error('加载新闻时出错:', err);
        });
    },
    loadCategories() {
      this.$api.getNewsCategories()
        .then(res => {
          this.categories = res.data?.categories || res.categories || [];
        })
        .catch(err => {
          console.error('加载类别失败:', err);
          // 即使分类加载失败也不影响主流程
        });
    },
    doSearch() {
    },
    toggleStatus(news) {
      const newStatus = news.status === 'active' ? 'inactive' : 'active';
      this.$api.adminUpdateNews(news.news_id, { status: newStatus })
        .then(() => {
          news.status = newStatus;
        })
        .catch(err => {
          this.error = `更新新闻 ${news.news_id} 状态失败: ${err.message || '未知错误'}`;
          console.error('更新新闻状态时出错:', err);
        });
    },
    editNews(news) {
      this.editingNews = { ...news };
      this.showEditDialog = true;
    },
    saveEditNews() {
      this.$api.adminUpdateNews(this.editingNews.news_id, {
        title: this.editingNews.title,
        abstract: this.editingNews.abstract,
        body: this.editingNews.body,
        category: this.editingNews.category,
        subcategory: this.editingNews.subcategory,
      })
        .then(() => {
          const idx = this.newsItems.findIndex(n => n.news_id === this.editingNews.news_id);
          if (idx > -1) {
            this.newsItems[idx] = { ...this.editingNews };
          }
          const fidx = this.flaggedNews.findIndex(n => n.news_id === this.editingNews.news_id);
          if (fidx > -1) {
            this.flaggedNews[fidx] = { ...this.editingNews };
          }
          this.showEditDialog = false;
        })
        .catch(err => {
          this.error = `保存新闻失败: ${err.message || '未知错误'}`;
          console.error('保存新闻时出错:', err);
        });
    },
    cancelEdit() {
      this.showEditDialog = false;
    },
    deleteNews(news) {
      if (!confirm(`确定删除新闻 "${news.title}" 吗？`)) return;
      this.$api.adminDeleteNews(news.news_id)
        .then(() => {
          const idx = this.newsItems.findIndex(n => n.news_id === news.news_id);
          if (idx > -1) this.newsItems.splice(idx, 1);
          const fidx = this.flaggedNews.findIndex(n => n.news_id === news.news_id);
          if (fidx > -1) this.flaggedNews.splice(fidx, 1);
        })
        .catch(err => {
          this.error = `删除新闻失败: ${err.message || '未知错误'}`;
          console.error('删除新闻时出错:', err);
        });
    }
  }
};
</script>

<style scoped>
.news-management-page {
  padding: 20px;
}

.management-container {
  max-width: 1200px;
  margin: 0 auto;
}

.title-row {
  display: flex;
  align-items: center;
  margin-bottom: 30px;
}

.title-group {
  display: flex;
  align-items: center;
  gap: 15px;
}

.title-icon {
  width: 32px;
  height: 32px;
  color: #333;
}

.title-icon svg {
  width: 100%;
  height: 100%;
}

.title-row h2 {
  margin: 0;
  font-size: 24px;
  color: #333;
}

.loading {
  text-align: center;
  padding: 20px;
  color: #666;
  font-size: 14px;
}

.error {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 15px;
  margin-bottom: 20px;
  background-color: #f8d7da;
  border: 1px solid #f5c6cb;
  border-radius: 4px;
  color: #721c24;
}

.error svg {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.section-container {
  background: #fff;
  padding: 32px;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  border: 1px solid #e2e8f0;
}
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  flex-wrap: wrap;
  gap: 10px;
}

.section-header h3 {
  margin: 0;
  font-size: 16px;
  color: #333;
}

.header-controls {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.search-input,
.filter-select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 13px;
}

.search-input {
  min-width: 150px;
}

.filter-select {
  min-width: 100px;
}

.btn-search {
  padding: 8px 16px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
}

.btn-search:hover {
  background-color: #0056b3;
}

.count-badge {
  background-color: #f0ad4e;
  color: white;
  padding: 5px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
}

.flagged-news-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.flagged-news-item {
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background-color: white;
  transition: all 0.3s ease;
}

.flagged-news-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.flagged-badge {
  background-color: #d9534f;
  color: white;
  padding: 4px 8px;
  border-radius: 3px;
  font-size: 12px;
}

.status-badge {
  padding: 4px 8px;
  border-radius: 3px;
  font-size: 12px;
  font-weight: bold;
}

.status-badge.active {
  background-color: #d4edda;
  color: #155724;
}

.status-badge.inactive {
  background-color: #f8d7da;
  color: #721c24;
}

.flagged-title {
  font-size: 14px;
  font-weight: bold;
  margin: 8px 0;
  color: #333;
}

.flagged-abstract {
  font-size: 13px;
  color: #666;
  margin: 8px 0;
  line-height: 1.4;
}

.item-actions {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}

.btn-mini {
  padding: 6px 12px;
  border: none;
  border-radius: 3px;
  font-size: 12px;
  cursor: pointer;
  background-color: #007bff;
  color: white;
  transition: background-color 0.2s;
}

.btn-mini:hover {
  background-color: #0056b3;
}

.btn-mini.btn-delete {
  background-color: #dc3545;
}

.btn-mini.btn-delete:hover {
  background-color: #c82333;
}

.btn-mini.btn-warning {
  background-color: #77ad63;
  color: #333;
}

.btn-mini.btn-warning:hover {
  background-color: #e0a800;
}

.btn-mini.btn-danger {
  background-color: #6c757d;
}

.btn-mini.btn-danger:hover {
  background-color: #5a6268;
}

.table-wrap {
  overflow-x: auto;
  margin-top: 15px;
}

.table {
  width: 100%;
  border-collapse: collapse;
  background-color: white;
  border: 1px solid #ddd;
  border-radius: 4px;
  overflow: hidden;
}

.table thead {
  background-color: #f8f9fa;
  border-bottom: 2px solid #ddd;
}

.table th {
  padding: 12px;
  text-align: left;
  font-weight: bold;
  color: #333;
  font-size: 13px;
}

.table td {
  padding: 12px;
  border-bottom: 1px solid #eee;
  font-size: 13px;
}

.table tbody tr:hover {
  background-color: #f9f9f9;
}

.table .mono {
  font-family: monospace;
  font-size: 12px;
  color: #666;
}

.table .title {
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.category-tag {
  display: inline-block;
  padding: 4px 8px;
  background-color: #e7f3ff;
  color: #0066cc;
  border-radius: 3px;
  font-size: 12px;
}

.pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: bold;
}

.pill.active {
  background-color: #d4edda;
  color: #155724;
}

.pill.inactive {
  background-color: #f8d7da;
  color: #721c24;
}

.status-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: currentColor;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 15px;
  margin-top: 20px;
  padding: 15px;
  background-color: white;
  border-radius: 4px;
}

.btn-page {
  padding: 8px 16px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
}

.btn-page:hover:not(:disabled) {
  background-color: #0056b3;
}

.btn-page:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.page-info {
  font-size: 13px;
  color: #666;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #999;
  font-size: 14px;
}

.animate-shake {
  animation: shake 0.5s;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-5px); }
  75% { transform: translateX(5px); }
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #eee;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.modal-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #999;
}

.modal-close:hover {
  color: #333;
}

.modal-body {
  padding: 20px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
  color: #333;
  font-size: 14px;
}

.form-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  box-sizing: border-box;
}

.form-input:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 20px;
  border-top: 1px solid #eee;
}

.btn-cancel {
  padding: 8px 16px;
  background-color: #f0f0f0;
  color: #333;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.btn-cancel:hover {
  background-color: #e0e0e0;
}

.btn-save {
  padding: 8px 16px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.btn-save:hover {
  background-color: #0056b3;
}
</style>
