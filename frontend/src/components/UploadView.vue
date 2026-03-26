<template>
  <main class="upload-page">
    <div class="upload-container">
      <!-- 标题区域 -->
      <div class="upload-header">
        <div class="header-content">
          <div class="header-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
              <polyline points="17,8 12,3 7,8"/>
              <line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
          </div>
          <div class="header-text">
            <h2>上传新闻</h2>
          </div>
        </div>
        <!-- 上传文件按钮 - 右上角 -->
        <button 
          type="button" 
          class="upload-file-btn"
          @click="$refs.fileInput.click()"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
            <polyline points="17,8 12,3 7,8"/>
            <line x1="12" y1="3" x2="12" y2="15"/>
          </svg>
          从文件上传
        </button>
        <input
          ref="fileInput"
          type="file"
          accept=".csv"
          style="display: none"
          @change="handleFileSelect"
        >
      </div>

      <!-- 主要内容区域 - 表单 + 列表 -->
      <div class="upload-main-content">
        <!-- 左侧表单 -->
        <div class="upload-form-section">
          <div class="upload-form">
            <div class="form-group">
              <label>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                  <polyline points="14,2 14,8 20,8"/>
                  <line x1="16" y1="13" x2="8" y2="13"/>
                  <line x1="16" y1="17" x2="8" y2="17"/>
                </svg>
                标题
              </label>
              <div class="input-wrapper">
                <input 
                  :value="uploadTitle" 
                  type="text" 
                  placeholder="输入新闻标题" 
                  @input="$emit('update:uploadTitle', $event.target.value)"
                >
              </div>
            </div>

            <div class="form-group">
              <label>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="17" y1="10" x2="3" y2="10"/>
                  <line x1="21" y1="6" x2="3" y2="6"/>
                  <line x1="21" y1="14" x2="3" y2="14"/>
                  <line x1="17" y1="18" x2="3" y2="18"/>
                </svg>
                摘要
              </label>
              <div class="input-wrapper">
                <textarea 
                  :value="uploadAbstract" 
                  placeholder="输入新闻摘要内容"
                  rows="3"
                  @input="$emit('update:uploadAbstract', $event.target.value)"
                ></textarea>
              </div>
            </div>

            <div class="form-group">
              <label>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                  <path d="M14 2v6h6"/>
                </svg>
                正文内容
              </label>
              <div class="input-wrapper">
                <textarea 
                  :value="uploadBody" 
                  placeholder="输入完整的新闻正文内容"
                  class="upload-body"
                  rows="6"
                  @input="$emit('update:uploadBody', $event.target.value)"
                ></textarea>
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="3" width="7" height="7"/>
                    <rect x="14" y="3" width="7" height="7"/>
                    <rect x="14" y="14" width="7" height="7"/>
                    <rect x="3" y="14" width="7" height="7"/>
                  </svg>
                  类别
                </label>
                <div class="input-wrapper">
                  <input 
                    :value="uploadCategory" 
                    type="text" 
                    placeholder="如: Sports"
                    @input="$emit('update:uploadCategory', $event.target.value)"
                  >
                </div>
              </div>

              
            </div>
            <div class="form-row">  
              <div class="form-group">
                <label>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/>
                  </svg>
                  标签
                </label>
                <div class="input-wrapper">
                  <input 
                    :value="uploadSubcategory" 
                    type="text" 
                    placeholder=""
                    @input="$emit('update:uploadSubcategory', $event.target.value)"
                  >
                </div>
              </div>
            </div>
            

            <div class="upload-actions">
              <button type="button" class="btn-secondary" @click="$emit('autoRecognize')">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 2v6h-6"/>
                  <path d="M3 12a9 9 0 0115-6.7L21 8"/>
                  <path d="M3 22v-6h6"/>
                  <path d="M21 12a9 9 0 01-15 6.7L3 16"/>
                </svg>
                自动识别类别
              </button>
              <button type="button" class="btn-primary" @click="$emit('submit')">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
                  <polyline points="17,8 12,3 7,8"/>
                  <line x1="12" y1="3" x2="12" y2="15"/>
                </svg>
                提交上传
              </button>
            </div>
          </div>
        </div>

        <!-- 右侧新闻列表 -->
        <div class="news-list-section" v-if="batchNewsList && batchNewsList.length > 0">
          <div class="news-list-header">
            <h3>新闻列表 ({{ batchNewsList.length }} 条)</h3>
          </div>
          <div class="news-list">
            <div 
              v-for="(news, index) in batchNewsList" 
              :key="index"
              class="news-list-item"
              :class="{ 'selected': selectedNewsIndex === index }"
              @click="selectNews(index)"
            >
              <div class="news-title">{{ news.title || `新闻 ${index + 1}` }}</div>
              <div class="news-category" v-if="news.category">
                {{ news.category }}{{ news.subcategory ? ` / ${news.subcategory}` : '' }}
              </div>
              <div class="news-abstract" v-if="news.abstract">
                {{ news.abstract.substring(0, 80) }}{{ news.abstract.length > 80 ? '...' : '' }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 错误提示 -->
      <p v-if="uploadError" class="error animate-shake">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <line x1="15" y1="9" x2="9" y2="15"/>
          <line x1="9" y1="15" x2="15" y2="9"/>
        </svg>
        {{ uploadError }}
      </p>
    </div>
  </main>
</template>

<script>
export default {
  name: 'UploadView',
  props: {
    uploadTitle: { type: String, default: '' },
    uploadAbstract: { type: String, default: '' },
    uploadBody: { type: String, default: '' },
    uploadCategory: { type: String, default: '' },
    uploadSubcategory: { type: String, default: '' },
    uploadResult: { type: String, default: '' },
    uploadError: { type: String, default: '' },
    batchNewsList: { type: Array, default: () => [] },
    selectedNewsIndex: { type: Number, default: -1 }
  },
  emits: [
    'update:uploadTitle', 'update:uploadAbstract', 'update:uploadBody',
    'update:uploadCategory', 'update:uploadSubcategory',
    'autoRecognize', 'submit', 'batch-upload', 'select-news'
  ],
  data() {
    return {
      isDragging: false
    }
  },
  methods: {
    handleFileSelect(e) {
      const files = e.target.files
      if (files.length > 0) this.uploadFile(files[0])
    },
    uploadFile(file) {
      if (!file.name.endsWith('.csv')) {
        this.$emit('batch-upload', { error: '仅支持 CSV 文件' })
        return
      }
      const reader = new FileReader()
      reader.onload = (e) => {
        try {
          const csv = e.target.result
          const rows = this.parseCSV(csv)
          this.$emit('batch-upload', { rows })
        } catch (err) {
          this.$emit('batch-upload', { error: 'CSV 解析失败: ' + err.message })
        }
      }
      reader.readAsText(file)
    },
    parseCSV(csv) {
      const rows = []
      let inQuotes = false
      let current = ''
      let headers = null
      let row = []
      
      for (let i = 0; i < csv.length; i++) {
        const char = csv[i]
        const nextChar = csv[i + 1]
        
        if (char === '"') {
          if (inQuotes && nextChar === '"') {
            current += '"'
            i++
          } else {
            inQuotes = !inQuotes
          }
        } else if (char === ',' && !inQuotes) {
          row.push(current.trim())
          current = ''
        } else if ((char === '\n' || char === '\r') && !inQuotes) {
          if (current.trim() || row.length > 0) {
            row.push(current.trim())
            if (!headers) {
              headers = row.map(h => h.toLowerCase().replace(/^"|"$/g, ''))
            } else if (row.some(v => v)) {
              const obj = {}
              headers.forEach((h, idx) => {
                obj[h] = (row[idx] || '').replace(/^"|"$/g, '')
              })
              rows.push(obj)
            }
            row = []
            current = ''
          }
          if (char === '\r' && nextChar === '\n') i++
        } else {
          current += char
        }
      }
      
      if (current.trim() || row.length > 0) {
        row.push(current.trim())
        if (headers && row.some(v => v)) {
          const obj = {}
          headers.forEach((h, idx) => {
            obj[h] = (row[idx] || '').replace(/^"|"$/g, '')
          })
          rows.push(obj)
        }
      }
      
      return rows
    },
    selectNews(index) {
      this.$emit('select-news', index)
    }
  }
}
</script>

<style scoped>
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-5px); }
  75% { transform: translateX(5px); }
}

.upload-page { 
  max-width: 1200px; 
  margin: 0 auto; 
  box-sizing: border-box; 
}

.upload-container {
  background: #fff;
  padding: 32px;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  border: 1px solid #e2e8f0;
}

/* 标题 */
.upload-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
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
  background: linear-gradient(135deg, #f59e0b 0%, #f97316 100%);
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 6px 16px rgba(245, 158, 11, 0.35);
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

/* 上传文件按钮 */
.upload-file-btn {
  padding: 10px 16px;
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.3);
}

.upload-file-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
}

.upload-file-btn svg {
  width: 18px;
  height: 18px;
}

/* 主要内容区域 */
.upload-main-content {
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: 32px;
  min-height: 400px;
}

/* 表单区域 */
.upload-form-section {
  /* 左侧表单保持原有样式 */
}

.upload-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.form-group label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #475569;
}

.form-group label svg {
  width: 18px;
  height: 18px;
  color: #6366f1;
}

.input-wrapper {
  position: relative;
}

.input-wrapper input,
.input-wrapper textarea {
  width: 100%;
  padding: 14px 16px;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  font-size: 15px;
  background: #f8fafc;
  box-sizing: border-box;
  transition: all 0.2s ease;
  font-family: inherit;
}

.input-wrapper textarea {
  resize: vertical;
  min-height: 100px;
  line-height: 1.5;
}

.input-wrapper input:focus,
.input-wrapper textarea:focus {
  outline: none;
  border-color: #6366f1;
  background: #fff;
  box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1);
}

.input-wrapper input::placeholder,
.input-wrapper textarea::placeholder {
  color: #94a3b8;
}

/* 按钮组 */
.upload-actions { 
  display: flex; 
  gap: 14px; 
  margin-top: 12px;
}

.btn-primary,
.btn-secondary {
  padding: 14px 24px;
  border: none;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  transition: all 0.2s ease;
}

.btn-primary {
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
  color: #fff;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.35);
  flex: 1;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(99, 102, 241, 0.45);
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

.btn-primary svg,
.btn-secondary svg {
  width: 18px;
  height: 18px;
}

/* 新闻列表区域 */
.news-list-section {
  background: #f8fafc;
  border-radius: 12px;
  padding: 16px;
  border: 1px solid #e2e8f0;
  max-height: 600px;
  overflow-y: auto;
}

.news-list-header {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 2px solid #e2e8f0;
}

.news-list-header h3 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: #1e293b;
}

.news-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.news-list-item {
  padding: 12px;
  background: white;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  cursor: pointer;
  transition: all 0.2s ease;
}

.news-list-item:hover {
  border-color: #6366f1;
  background: #f1f5f9;
}

.news-list-item.selected {
  border-color: #6366f1;
  background: #eef2ff;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
}

.news-title {
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 4px;
  font-size: 14px;
  line-height: 1.4;
}

.news-category {
  font-size: 12px;
  color: #6366f1;
  margin-bottom: 4px;
}

.news-abstract {
  font-size: 12px;
  color: #64748b;
  line-height: 1.4;
}

/* 错误提示 */
.error {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 20px;
  padding: 14px 18px;
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
  border-radius: 12px;
  color: #dc2626;
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

/* 响应式设计 */
@media (max-width: 768px) {
  .upload-main-content {
    grid-template-columns: 1fr;
    gap: 24px;
  }
  
  .upload-header {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }
  
  .upload-file-btn {
    align-self: flex-end;
  }
  
  .news-list-section {
    max-height: 300px;
  }
}
</style>
