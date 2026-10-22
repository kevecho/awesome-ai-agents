<template>
  <div class="consult-page">
    <!-- Chat Header -->
    <header class="chat-header">
      <button class="back-btn" @click="$router.push('/')">
        <el-icon :size="20">
          <ArrowLeft />
        </el-icon>
        <span>返回</span>
      </button>
      <div class="chat-header-center">
        <div class="chat-header-avatar">
          <svg width="36" height="36" viewBox="0 0 64 64" fill="none">
            <circle cx="32" cy="32" r="30" fill="url(#conG)" fill-opacity="0.1" stroke="url(#conG)" stroke-width="2" />
            <path
              d="M20 18H44C46.2 18 48 19.8 48 22V40C48 42.2 46.2 44 44 44H36L32 48L28 44H20C17.8 44 16 42.2 16 40V22C16 19.8 17.8 18 20 18Z"
              fill="url(#conG)" fill-opacity="0.08" stroke="url(#conG)" stroke-width="2" stroke-linecap="round" />
            <path d="M30 26V34M26 30H34" stroke="url(#conG)" stroke-width="2.5" stroke-linecap="round" />
            <circle cx="20" cy="20" r="2.5" fill="#4F8DFF" fill-opacity="0.25" />
            <circle cx="44" cy="20" r="2.5" fill="#3A6FD9" fill-opacity="0.25" />
            <circle cx="44" cy="44" r="2.5" fill="#3A6FD9" fill-opacity="0.25" />
            <defs>
              <linearGradient id="conG" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stop-color="#4F8DFF" />
                <stop offset="100%" stop-color="#3A6FD9" />
              </linearGradient>
            </defs>
          </svg>
        </div>
        <div class="chat-header-info">
          <span class="chat-header-name">AI 医疗助手</span>
          <span class="chat-header-status">在线</span>
        </div>
      </div>
      <div class="chat-header-actions">
        <el-dropdown trigger="click" @command="handleMenuCommand">
          <el-button circle class="header-action-btn">
            <el-icon :size="18">
              <MoreFilled />
            </el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="end" :disabled="consultation?.status === 'completed'">
                <el-icon>
                  <CircleCheck />
                </el-icon>
                {{ consultation?.status === 'completed' ? '已结束' : '结束问诊' }}
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </header>

    <!-- Chat Messages -->
    <main class="chat-main" ref="chatMainRef">
      <div class="message-list" ref="messageListRef">
        <!-- Welcome Message -->
        <div v-if="messages.length === 0 && !streaming" class="welcome-message">
          <div class="welcome-avatar">
            <svg width="72" height="72" viewBox="0 0 64 64" fill="none">
              <circle cx="32" cy="32" r="30" fill="url(#conG)" fill-opacity="0.1" stroke="url(#conG)"
                stroke-width="2" />
              <path
                d="M20 18H44C46.2 18 48 19.8 48 22V40C48 42.2 46.2 44 44 44H36L32 48L28 44H20C17.8 44 16 42.2 16 40V22C16 19.8 17.8 18 20 18Z"
                fill="url(#conG)" fill-opacity="0.08" stroke="url(#conG)" stroke-width="2" stroke-linecap="round" />
              <path d="M30 26V34M26 30H34" stroke="url(#conG)" stroke-width="2.5" stroke-linecap="round" />
              <circle cx="20" cy="20" r="2.5" fill="#4F8DFF" fill-opacity="0.25" />
              <circle cx="44" cy="20" r="2.5" fill="#3A6FD9" fill-opacity="0.25" />
              <circle cx="44" cy="44" r="2.5" fill="#3A6FD9" fill-opacity="0.25" />
              <defs>
                <linearGradient id="conG" x1="0" y1="0" x2="1" y2="1">
                  <stop offset="0%" stop-color="#4F8DFF" />
                  <stop offset="100%" stop-color="#3A6FD9" />
                </linearGradient>
              </defs>
            </svg>
          </div>
          <h3 class="welcome-title">您好，我是小医</h3>
          <p class="welcome-desc">请描述您的症状，我将为您提供初步的健康建议。</p>
          <p class="welcome-disclaimer">⚠️ 本系统由 AI 驱动，仅供参考，不构成医疗建议。</p>
          <!-- Quick Replies -->
          <div class="quick-replies">
            <div class="quick-reply-chip" @click="sendQuickReply('我头疼两天了，还有点发烧')">
              <el-icon :size="14">
                <ColdDrink />
              </el-icon> 头疼发烧
            </div>
            <div class="quick-reply-chip" @click="sendQuickReply('我最近总是胃疼，吃饭后更明显')">
              <el-icon :size="14">
                <KnifeFork />
              </el-icon> 胃部不适
            </div>
            <div class="quick-reply-chip" @click="sendQuickReply('我最近睡不着觉，总是失眠')">
              <el-icon :size="14">
                <Moon />
              </el-icon> 失眠
            </div>
            <div class="quick-reply-chip" @click="sendQuickReply('我喉咙痛好几天了，咳嗽有痰')">
              <el-icon :size="14">
                <Microphone />
              </el-icon> 咽喉痛
            </div>
          </div>
        </div>

        <!-- Messages -->
        <div v-for="(msg, i) in messages" :key="i"
          :class="['message-item', msg.role === 'user' ? 'user-msg' : 'ai-msg']"
          :style="{ animationDelay: i * 0.05 + 's' }">
          <div class="message-avatar">
            <template v-if="msg.role === 'user'">
              <div class="user-avatar-badge">{{ userStore.username?.charAt(0).toUpperCase() || 'U' }}</div>
            </template>
            <template v-else>
              <svg width="36" height="36" viewBox="0 0 64 64" fill="none">
                <circle cx="32" cy="32" r="30" fill="url(#conG)" fill-opacity="0.1" stroke="url(#conG)"
                  stroke-width="2" />
                <path
                  d="M22 20H42C43.1 20 44 20.9 44 22V38C44 39.1 43.1 40 42 40H36L32 44L28 40H22C20.9 40 20 39.1 20 38V22C20 20.9 20.9 20 22 20Z"
                  fill="url(#conG)" fill-opacity="0.08" stroke="url(#conG)" stroke-width="2" stroke-linecap="round" />
                <path d="M30 26V32M28 29H32" stroke="url(#conG)" stroke-width="2" stroke-linecap="round" />
                <defs>
                  <linearGradient id="conG" x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0%" stop-color="#4F8DFF" />
                    <stop offset="100%" stop-color="#3A6FD9" />
                  </linearGradient>
                </defs>
              </svg>
            </template>
          </div>
          <div class="message-content">
            <div class="message-bubble" v-html="renderContent(msg.content)"></div>
            <div v-if="msg.metadata?.urgency" class="message-triage">
              <span :class="['triage-tag', msg.metadata.urgency]">
                🏥 {{ msg.metadata.department || '建议就医' }} · {{ urgencyText(msg.metadata.urgency) }}
              </span>
            </div>
          </div>
        </div>

        <!-- Streaming Message -->
        <div v-if="streaming" class="message-item ai-msg streaming-msg">
          <div class="message-avatar">
            <svg width="36" height="36" viewBox="0 0 64 64" fill="none">
              <circle cx="32" cy="32" r="30" fill="#4F8DFF" fill-opacity="0.08" />
              <path d="M32 22V42M22 32H42" stroke="#4F8DFF" stroke-width="2.5" stroke-linecap="round" />
            </svg>
          </div>
          <div class="message-content">
            <div class="message-bubble streaming-bubble" v-html="renderContent(streamText)"></div>
            <div class="typing-indicator" v-if="streamText.length === 0">
              <span class="typing-dot"></span>
              <span class="typing-dot"></span>
              <span class="typing-dot"></span>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- Completed Banner -->
    <div v-if="consultation?.status === 'completed'" class="completed-banner">
      <el-icon :size="18">
        <CircleCheck />
      </el-icon>
      <span>本次问诊已结束，您可以返回首页查看历史记录</span>
    </div>

    <!-- Input Area -->
    <footer class="chat-footer" v-if="consultation?.status !== 'completed'">
      <div class="input-wrapper">
        <button class="voice-btn" title="语音输入">
          <el-icon :size="20">
            <Microphone />
          </el-icon>
        </button>
        <textarea v-model="inputText" :placeholder="streaming ? 'AI 正在回复...' : '请描述您的症状（例如：我头疼两天了...）'"
          :disabled="streaming" class="message-input" rows="1" @keydown.enter.prevent="sendMessage"
          @input="autoResize" />
        <button class="send-btn" :class="{ active: inputText.trim() && !streaming }"
          :disabled="!inputText.trim() || streaming" @click="sendMessage">
          <el-icon :size="20">
            <Promotion />
          </el-icon>
        </button>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useConsultStore } from '../stores/useConsultStore'
import { useUserStore } from '../stores/useUserStore'
import { ArrowLeft, MoreFilled, Promotion, Microphone, ColdDrink, KnifeFork, Moon, CircleCheck } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import MarkdownIt from 'markdown-it'

const route = useRoute()
const consultStore = useConsultStore()
const userStore = useUserStore()

const messages = ref([])
const consultation = ref(null)
const inputText = ref('')
const streaming = ref(false)
const streamText = ref('')
const messageListRef = ref(null)
const chatMainRef = ref(null)

const ws = ref(null)
const md = new MarkdownIt({ breaks: true, html: true })

onMounted(async () => {
  const id = route.params.id
  await consultStore.fetchConsultation(id)
  consultation.value = consultStore.currentConsultation
  messages.value = consultStore.messages.map(m => ({
    ...m,
    metadata: m.metadata_json,
  }))
  scrollToBottom()
})

function renderContent(text) {
  if (!text) return ''
  return md.render(text)
}

function autoResize(e) {
  const el = e.target
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 120) + 'px'
}

function sendQuickReply(text) {
  inputText.value = text
  sendMessage()
}

function sendMessage() {
  if (!inputText.value.trim() || streaming.value) return

  const text = inputText.value.trim()
  inputText.value = ''
  messages.value.push({ role: 'user', content: text })
  scrollToBottom()
  connectWebSocket(text)
}

function connectWebSocket(userMessage) {
  const token = userStore.token
  const consultationId = route.params.id
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = "localhost:18080" //window.location.host

  const url = `${protocol}//${host}/api/ws/chat?token=${token}`
  const socket = new WebSocket(url)
  ws.value = socket

  streaming.value = true
  streamText.value = ''

  socket.onopen = () => {
    socket.send(JSON.stringify({
      consultation_id: parseInt(consultationId),
      message: userMessage,
    }))
  }

  socket.onmessage = (event) => {
    const chunk = JSON.parse(event.data)
    const chunkType = chunk.type

    if (chunkType === 'token') {
      streamText.value += chunk.content
      scrollToBottom()
    } else if (chunkType === 'complete') {
      messages.value.push({
        role: 'assistant',
        content: streamText.value,
        metadata: chunk.metadata,
      })
      streamText.value = ''
      streaming.value = false
      socket.close()
      scrollToBottom()
    } else if (chunkType === 'error') {
      messages.value.push({
        role: 'assistant',
        content: `❌ ${chunk.content}`,
      })
      streaming.value = false
      socket.close()
    }
  }

  socket.onerror = () => {
    if (streamText.value) {
      messages.value.push({ role: 'assistant', content: streamText.value })
    } else {
      messages.value.push({
        role: 'assistant',
        content: '❌ 连接失败，请稍后重试。',
      })
    }
    streamText.value = ''
    streaming.value = false
  }

  socket.onclose = () => {
    streaming.value = false
    const inputEl = document.querySelector('.message-input')
    if (inputEl) { inputEl.style.height = 'auto' }
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (messageListRef.value) {
      messageListRef.value.scrollTop = messageListRef.value.scrollHeight
    }
  })
}

function urgencyText(urgency) {
  const map = { normal: '正常', urgent: '建议尽快就医', emergency: '紧急！立即就医' }
  return map[urgency] || ''
}

async function handleMenuCommand(command) {
  if (command === 'end') {
    try {
      await ElMessageBox.confirm(
        '结束后将无法继续发送消息，确定要结束本次问诊吗？',
        '结束问诊',
        { confirmButtonText: '确定结束', cancelButtonText: '取消', type: 'warning' }
      )
      await consultStore.completeConsultation(route.params.id)
      consultation.value = { ...consultation.value, status: 'completed' }
      ElMessage.success('问诊已结束')
    } catch {
      // cancelled
    }
  }
}
</script>

<style scoped>
.consult-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: linear-gradient(135deg, #f0f2f5 0%, #e8ecf5 50%, #e4eaf5 100%);
  font-family: 'Inter', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

/* ========= Chat Header ========= */
.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  padding: 0 20px;
  height: 64px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
  flex-shrink: 0;
  z-index: 10;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  background: none;
  border: none;
  font-size: 14px;
  color: #4F8DFF;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 10px;
  transition: all 0.2s;
}

.back-btn:hover {
  background: rgba(79, 141, 255, 0.08);
}

.chat-header-center {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chat-header-avatar {
  display: flex;
}

.chat-header-info {
  display: flex;
  flex-direction: column;
}

.chat-header-name {
  font-size: 15px;
  font-weight: 600;
  color: #1a1a2e;
}

.chat-header-status {
  font-size: 12px;
  color: #34C759;
}

.header-action-btn {
  width: 40px;
  height: 40px;
  border: none;
  background: #f5f7fa;
  border-radius: 10px;
  transition: all 0.2s;
}

.header-action-btn:hover {
  background: #e8ecf1;
}

/* ========= Chat Main ========= */
.chat-main {
  flex: 1;
  overflow-y: auto;
  padding: 24px 0;
}

.message-list {
  max-width: 800px;
  margin: 0 auto;
  padding: 0 24px;
}

/* ========= Welcome Message ========= */
.welcome-message {
  text-align: center;
  padding: 40px 20px 20px;
  animation: fadeInUp 0.6s ease-out;
}

.welcome-avatar {
  margin-bottom: 20px;
  animation: float 6s ease-in-out infinite;
}

.welcome-title {
  font-size: 22px;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 8px;
}

.welcome-desc {
  font-size: 14px;
  color: #666;
  margin-bottom: 6px;
}

.welcome-disclaimer {
  font-size: 12px;
  color: #FF9500;
  margin-bottom: 24px;
}

/* Quick Reply Chips */
.quick-replies {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 10px;
  max-width: 480px;
  margin: 0 auto;
}

.quick-reply-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 18px;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.4);
  border-radius: 20px;
  font-size: 13px;
  color: #555;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
}

.quick-reply-chip:hover {
  border-color: #4F8DFF;
  background: rgba(79, 141, 255, 0.05);
  color: #4F8DFF;
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(79, 141, 255, 0.12);
}

/* ========= Messages ========= */
.message-item {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  animation: fadeInUp 0.4s ease-out;
  opacity: 0;
  animation-fill-mode: forwards;
}

.user-msg {
  flex-direction: row-reverse;
}

.ai-msg {
  flex-direction: row;
}

.message-avatar {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-avatar-badge {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, #4F8DFF, #3A6FD9);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 14px;
  font-weight: 600;
}

.message-content {
  max-width: 65%;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.message-bubble {
  padding: 14px 18px;
  font-size: 14px;
  line-height: 1.7;
  word-break: break-word;
  position: relative;
}

.user-msg .message-bubble {
  background: linear-gradient(135deg, #4F8DFF 0%, #5B8CFF 100%);
  color: white;
  border-radius: 18px 4px 18px 18px;
  box-shadow: 0 4px 15px rgba(79, 141, 255, 0.2);
}

.ai-msg .message-bubble {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  color: #303133;
  border-radius: 4px 18px 18px 18px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.06);
  border-left: 3px solid #4F8DFF;
}

/* Markdown Content Styling */
.message-bubble :deep(p) {
  margin: 0 0 8px;
}

.message-bubble :deep(p:last-child) {
  margin-bottom: 0;
}

.message-bubble :deep(ul),
.message-bubble :deep(ol) {
  padding-left: 20px;
  margin: 8px 0;
}

.message-bubble :deep(li) {
  margin-bottom: 4px;
}

.message-bubble :deep(code) {
  background: rgba(0, 0, 0, 0.06);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
}

.user-msg .message-bubble :deep(code) {
  background: rgba(255, 255, 255, 0.15);
  color: white;
}

.message-bubble :deep(pre code) {
  display: block;
  padding: 12px;
  overflow-x: auto;
}

.message-bubble :deep(strong) {
  font-weight: 600;
}

/* Triage Tags */
.message-triage {
  margin-top: 4px;
}

.triage-tag {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 500;
}

.triage-tag.normal {
  background: #E8F8E8;
  color: #2E7D32;
}

.triage-tag.urgent {
  background: #FFF3E0;
  color: #E65100;
}

.triage-tag.emergency {
  background: #FFEBEE;
  color: #C62828;
}

/* ========= Streaming ========= */
.streaming-msg .message-bubble {
  border-left-color: #34C759;
}

.typing-indicator {
  display: flex;
  gap: 6px;
  padding: 14px 18px;
  align-items: center;
}

.typing-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #4F8DFF;
  animation: typingDot 1.4s infinite;
}

.typing-dot:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-dot:nth-child(3) {
  animation-delay: 0.4s;
}

/* ========= Completed Banner ========= */
.completed-banner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 14px 24px;
  background: rgba(232, 248, 232, 0.8);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  color: #2E7D32;
  font-size: 14px;
  font-weight: 500;
  border-top: 1px solid rgba(200, 230, 201, 0.5);
  flex-shrink: 0;
}

/* ========= Chat Footer ========= */
.chat-footer {
  padding: 16px 24px 20px;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-top: 1px solid rgba(0, 0, 0, 0.04);
  flex-shrink: 0;
}

.input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  max-width: 800px;
  margin: 0 auto;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-radius: 16px;
  padding: 8px 8px 8px 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  transition: all 0.3s;
}

.input-wrapper:focus-within {
  border-color: #4F8DFF;
  background: rgba(255, 255, 255, 0.85);
  box-shadow: 0 0 0 4px rgba(79, 141, 255, 0.08);
}

.voice-btn {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  border: none;
  background: transparent;
  border-radius: 12px;
  cursor: pointer;
  color: #8E8E93;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.voice-btn:hover {
  background: rgba(255, 255, 255, 0.5);
  color: #4F8DFF;
}

.message-input {
  flex: 1;
  border: none;
  background: transparent;
  resize: none;
  font-size: 14px;
  line-height: 1.5;
  padding: 8px 0;
  max-height: 120px;
  font-family: inherit;
  outline: none;
  color: #1a1a2e;
}

.message-input::placeholder {
  color: #b0b0b8;
}

.send-btn {
  flex-shrink: 0;
  width: 44px;
  height: 44px;
  border: none;
  border-radius: 12px;
  background: #e8ecf1;
  color: #b0b0b8;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.send-btn.active {
  background: linear-gradient(135deg, #4F8DFF, #7C4DFF);
  color: white;
  box-shadow: 0 4px 12px rgba(79, 141, 255, 0.3);
}

.send-btn.active:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(79, 141, 255, 0.4);
}
</style>
