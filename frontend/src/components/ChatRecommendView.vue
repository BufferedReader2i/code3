<template>
  <main class="chat-recommend-main">
    <div class="chat-container">
      <!-- 标题 -->
      <div class="chat-header">
        <div class="header-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
          </svg>
        </div>
        <h2>智能对话推荐</h2>
        <p class="header-desc">用自然语言描述您的需求，AI为您精准推荐</p>
        <button v-if="messages.length > 0" class="btn-clear" @click="clearHistory">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="3 6 5 6 21 6"></polyline>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
          </svg>
          清除对话
        </button>
      </div>

      <!-- LLM状态提示 -->
      <div v-if="!llmReady" class="llm-status-warning">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="12" y1="8" x2="12" y2="12"></line>
          <line x1="12" y1="16" x2="12.01" y2="16"></line>
        </svg>
        <span>LLM服务未就绪，请确保Ollama已启动并下载了qwen3.5:4b模型</span>
      </div>

      <!-- 消息列表 -->
      <div class="messages-container" ref="messagesContainer">
        <div v-if="messages.length === 0" class="empty-state">
          <div class="empty-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
          </div>
          <h3>开始对话</h3>
          <p>试试以下示例：</p>
          <div class="suggestions">
            <button v-for="s in defaultSuggestions" :key="s" @click="sendSuggestion(s)">
              {{ s }}
            </button>
          </div>
        </div>

        <div v-for="(msg, index) in messages" :key="index" :class="['message', msg.role]">
          <div class="message-avatar">
            <span v-if="msg.role === 'user'">我</span>
            <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v1a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-1H2a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h1a7 7 0 0 1 7-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2z"></path>
              <circle cx="7.5" cy="14.5" r="1.5"></circle>
              <circle cx="16.5" cy="14.5" r="1.5"></circle>
            </svg>
          </div>
          <div class="message-content">
            <div class="message-text">{{ msg.content }}</div>
            
            <!-- 推荐结果 -->
            <div v-if="msg.recommendations && msg.recommendations.length > 0" class="recommendations-grid">
              <div 
                v-for="news in msg.recommendations" 
                :key="news.id" 
                class="news-item"
                @click="$emit('open-detail', news)"
              >
                <div class="news-category">{{ news.category }}</div>
                <div class="news-title">{{ news.title }}</div>
                <div class="news-abstract">{{ news.abstract }}</div>
              </div>
            </div>

            <!-- 追问建议 -->
            <div v-if="msg.suggestions && msg.suggestions.length > 0" class="followup-suggestions">
              <span>您可能还想问：</span>
              <button v-for="s in msg.suggestions" :key="s" @click="sendSuggestion(s)">
                {{ s }}
              </button>
            </div>
          </div>
        </div>

        <!-- 加载状态 -->
        <div v-if="loading" class="message assistant loading-message">
          <div class="message-avatar">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v1a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-1H2a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h1a7 7 0 0 1 7-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2z"></path>
            </svg>
          </div>
          <div class="message-content">
            <div class="loading-dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="input-area">
        <textarea
          v-model="inputMessage"
          @keydown.enter.exact.prevent="sendMessage"
          placeholder="描述您想看的内容，例如：给我推荐一些科技新闻..."
          rows="1"
          ref="inputTextarea"
        ></textarea>
        <button class="btn-send" @click="sendMessage" :disabled="loading || !inputMessage.trim()">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="22" y1="2" x2="11" y2="13"></line>
            <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
          </svg>
        </button>
      </div>
    </div>
  </main>
</template>

<script>
import { api } from '../api.js'
import { useAuth } from '../composables/useAuth.js'

export default {
  name: 'ChatRecommendView',
  emits: ['open-detail'],
  setup() {
    const { username } = useAuth()
    return { username }
  },
  data() {
    return {
      messages: [],
      inputMessage: '',
      loading: false,
      llmReady: true,
      defaultSuggestions: [
        '给我推荐一些体育新闻',
        '有什么娱乐类的资讯？',
        '最近有什么财经新闻？'
      ]
    }
  },
  async mounted() {
    await this.checkLLMStatus()
  },
  methods: {
    async checkLLMStatus() {
      try {
        const res = await api.getLLMStatus()
        this.llmReady = res.data.ready
      } catch (e) {
        this.llmReady = false
      }
    },
    async sendMessage() {
      if (!this.inputMessage.trim() || this.loading) return

      const userMessage = this.inputMessage.trim()
      this.inputMessage = ''

      // 添加用户消息
      this.messages.push({
        role: 'user',
        content: userMessage
      })

      this.loading = true
      this.scrollToBottom()

      // 添加AI消息占位
      const aiMessageIndex = this.messages.length
      this.messages.push({
        role: 'assistant',
        content: '',
        recommendations: [],
        suggestions: []
      })

      const userId = this.username || localStorage.getItem('username') || 'anonymous'
      
      try {
        const res = await api.llmChat(userMessage, userId)
        this.messages[aiMessageIndex].content = res.data.reply
        this.messages[aiMessageIndex].recommendations = res.data.recommendations || []
        this.messages[aiMessageIndex].suggestions = res.data.suggestions || []
      } catch (e) {
        this.messages[aiMessageIndex].content = '抱歉，服务出现了问题: ' + (e.message || '未知错误')
      } finally {
        this.loading = false
        this.scrollToBottom()
      }
    },
    sendSuggestion(s) {
      this.inputMessage = s
      this.sendMessage()
    },
    async clearHistory() {
      try {
        await api.clearLLMHistory()
        this.messages = []
      } catch (e) {
        console.error('清除历史失败', e)
      }
    },
    scrollToBottom() {
      this.$nextTick(() => {
        const container = this.$refs.messagesContainer
        if (container) {
          container.scrollTop = container.scrollHeight
        }
      })
    }
  }
}
</script>

<style scoped>
.chat-recommend-main {
  min-height: 100vh;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  padding: 20px;
}

.chat-container {
  max-width: 900px;
  margin: 0 auto;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 20px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  flex-direction: column;
  height: calc(100vh - 120px);
  min-height: 600px;
}

.chat-header {
  padding: 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.header-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.header-icon svg {
  width: 24px;
  height: 24px;
  color: white;
}

.chat-header h2 {
  color: #fff;
  margin: 0;
  font-size: 1.5rem;
}

.header-desc {
  color: rgba(255, 255, 255, 0.6);
  margin: 0;
  font-size: 0.875rem;
}

.btn-clear {
  margin-left: auto;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.8);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.875rem;
  transition: all 0.2s;
}

.btn-clear:hover {
  background: rgba(255, 255, 255, 0.15);
}

.btn-clear svg {
  width: 16px;
  height: 16px;
}

.llm-status-warning {
  padding: 12px 24px;
  background: rgba(255, 193, 7, 0.1);
  border-bottom: 1px solid rgba(255, 193, 7, 0.3);
  color: #ffc107;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 0.875rem;
}

.llm-status-warning svg {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.empty-icon {
  width: 80px;
  height: 80px;
  margin: 0 auto 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-icon svg {
  width: 40px;
  height: 40px;
  color: white;
}

.empty-state h3 {
  color: #fff;
  margin: 0 0 8px;
  font-size: 1.5rem;
}

.empty-state p {
  color: rgba(255, 255, 255, 0.6);
  margin: 0 0 20px;
}

.suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
}

.suggestions button {
  padding: 10px 20px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 20px;
  color: #fff;
  cursor: pointer;
  transition: all 0.2s;
}

.suggestions button:hover {
  background: rgba(102, 126, 234, 0.3);
  border-color: #667eea;
}

.message {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 0.875rem;
  font-weight: 600;
}

.message.user .message-avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.message.assistant .message-avatar {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.message.assistant .message-avatar svg {
  width: 20px;
  height: 20px;
  color: rgba(255, 255, 255, 0.8);
}

.message-content {
  max-width: 70%;
}

.message.user .message-content {
  text-align: right;
}

.message-text {
  background: rgba(255, 255, 255, 0.1);
  padding: 12px 16px;
  border-radius: 16px;
  color: #fff;
  line-height: 1.5;
}

.message.user .message-text {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-bottom-right-radius: 4px;
}

.message.assistant .message-text {
  border-bottom-left-radius: 4px;
}

.recommendations-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
  margin-top: 16px;
}

.news-item {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.news-item:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: #667eea;
  transform: translateY(-2px);
}

.news-category {
  font-size: 0.75rem;
  color: #667eea;
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.news-title {
  color: #fff;
  font-size: 0.9rem;
  font-weight: 500;
  margin-bottom: 6px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.news-abstract {
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.8rem;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.followup-suggestions {
  margin-top: 14px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.followup-suggestions span {
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.8rem;
}

.followup-suggestions button {
  padding: 6px 12px;
  background: rgba(102, 126, 234, 0.2);
  border: 1px solid rgba(102, 126, 234, 0.3);
  border-radius: 16px;
  color: #a8b4ff;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s;
}

.followup-suggestions button:hover {
  background: rgba(102, 126, 234, 0.3);
}

.loading-message .message-content {
  display: flex;
  align-items: center;
}

.loading-dots {
  display: flex;
  gap: 6px;
  padding: 12px 16px;
}

.loading-dots span {
  width: 8px;
  height: 8px;
  background: rgba(255, 255, 255, 0.5);
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.loading-dots span:nth-child(1) { animation-delay: -0.32s; }
.loading-dots span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.input-area {
  padding: 20px 24px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  gap: 12px;
}

.input-area textarea {
  flex: 1;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  padding: 12px 16px;
  color: #fff;
  font-size: 0.95rem;
  resize: none;
  outline: none;
  transition: all 0.2s;
  font-family: inherit;
}

.input-area textarea:focus {
  border-color: #667eea;
  background: rgba(255, 255, 255, 0.08);
}

.input-area textarea::placeholder {
  color: rgba(255, 255, 255, 0.4);
}

.btn-send {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.btn-send:hover:not(:disabled) {
  transform: scale(1.05);
}

.btn-send:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-send svg {
  width: 20px;
  height: 20px;
  color: white;
}

/* 滚动条样式 */
.messages-container::-webkit-scrollbar {
  width: 6px;
}

.messages-container::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
}

.messages-container::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
}

.messages-container::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}
</style>