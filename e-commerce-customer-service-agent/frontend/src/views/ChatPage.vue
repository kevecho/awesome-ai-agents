<template>
  <div class="chat-page">
    <header class="chat-header">
      <div class="header-info">
        <span class="bot-name">小E - 智能客服</span>
        <span class="status" :class="store.isConnected ? 'online' : 'offline'">
          {{ store.isConnected ? '在线' : '离线' }}
        </span>
      </div>
      <div class="header-actions">
        <el-button text @click="router.push('/history')">历史记录</el-button>
        <el-button text @click="router.push('/dashboard')">数据看板</el-button>
      </div>
    </header>

    <div v-if="store.currentSentiment" class="sentiment-bar" :class="store.currentSentiment">
      <span class="sentiment-label">{{ sentimentLabel }}</span>
    </div>

    <div class="chat-messages" ref="messagesRef">
      <div v-if="store.messages.length === 0" class="welcome">
        <div class="welcome-icon">CS</div>
        <h2>欢迎使用小E智能客服</h2>
        <p>我可以帮您查询订单、了解商品信息、处理退款退货等问题</p>
        <div class="quick-services">
          <el-button
            v-for="service in quickServices"
            :key="service.code"
            size="large"
            @click="handleSend(service.text)"
          >
            {{ service.name }}
          </el-button>
        </div>
      </div>

      <MessageBubble
        v-for="msg in store.messages"
        :key="msg.id"
        :message="msg"
      />

      <div v-if="store.isTyping" class="typing-indicator">
        <span></span><span></span><span></span>
      </div>
    </div>

    <QuickReplyBar
      v-if="store.quickReplies.length > 0"
      :replies="store.quickReplies"
      @select="handleSend"
    />

    <div class="chat-input-area">
      <el-input
        v-model="inputText"
        type="textarea"
        :rows="2"
        placeholder="请输入您的问题..."
        resize="none"
        @keydown.enter.exact.prevent="handleSend()"
      />
      <el-button
        type="primary"
        :disabled="!inputText.trim() || store.isTyping"
        @click="handleSend()"
      >
        发送
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useChatStore } from '@/stores/chat'
import MessageBubble from '@/components/MessageBubble.vue'
import QuickReplyBar from '@/components/QuickReplyBar.vue'
import type { QuickService } from '@/types/chat'

const router = useRouter()
const store = useChatStore()

const inputText = ref('')
const messagesRef = ref<HTMLElement>()

const quickServices: QuickService[] = [
  { code: 'order', name: '订单查询', text: '我想查一下我的订单' },
  { code: 'product', name: '商品咨询', text: '有什么推荐的商品吗？' },
  { code: 'refund', name: '退款退货', text: '如何申请退款退货？' },
  { code: 'human', name: '人工客服', text: '帮我转人工客服' },
]

const sentimentLabel = computed(() => {
  const labels: Record<string, string> = {
    positive: '用户情绪: 积极',
    neutral: '用户情绪: 平和',
    negative: '用户情绪: 需要关注',
  }
  return labels[store.currentSentiment || 'neutral'] || ''
})

async function handleSend(text?: string): Promise<void> {
  const content = text || inputText.value.trim()
  if (!content) return

  if (!store.isConnected) {
    await store.initSession()
  }

  inputText.value = ''
  await store.sendMessage(content)
  await nextTick()
  scrollToBottom()
}

function scrollToBottom(): void {
  if (messagesRef.value) {
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  }
}

onMounted(async () => {
  await store.initSession()
})
</script>

<style scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  max-width: 800px;
  margin: 0 auto;
  background: #ffffff;
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.05);
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

.bot-name {
  font-size: 16px;
  font-weight: 600;
}

.status {
  font-size: 11px;
  margin-left: 8px;
  padding: 2px 8px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.2);
}

.sentiment-bar {
  padding: 8px 20px;
  font-size: 12px;
  text-align: center;
}

.sentiment-bar.positive { background: #e8f5e9; color: #2e7d32; }
.sentiment-bar.neutral { background: #f5f5f5; color: #616161; }
.sentiment-bar.negative { background: #ffebee; color: #c62828; }

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #f8f9fa;
}

.welcome {
  text-align: center;
  padding: 60px 20px;
}

.welcome-icon {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
  font-size: 24px;
  font-weight: 700;
}

.welcome h2 { font-size: 20px; margin-bottom: 8px; color: #303133; }
.welcome p { color: #909399; margin-bottom: 24px; }

.quick-services { display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; }

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
  background: #fff;
  border-radius: 12px;
  width: fit-content;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.typing-indicator span {
  width: 8px; height: 8px;
  background: #ccd0d5;
  border-radius: 50%;
  animation: typingBounce 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

@keyframes typingBounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.chat-input-area {
  display: flex;
  gap: 10px;
  padding: 16px 20px;
  background: #fff;
  border-top: 1px solid #ebeef5;
}

.chat-input-area :deep(.el-textarea__inner) { border-radius: 8px; }
.chat-input-area .el-button { align-self: flex-end; border-radius: 8px; }
</style>
