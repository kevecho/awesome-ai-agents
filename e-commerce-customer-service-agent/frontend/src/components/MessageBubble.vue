<template>
  <div class="message-bubble" :class="message.isUser ? 'is-user' : 'is-bot'">
    <div v-if="!message.isUser" class="avatar bot-avatar">小E</div>

    <div class="bubble-wrapper">
      <div v-if="message.intent && !message.isUser" class="meta-tag">
        意图: {{ message.intent.intent_name }}
        <span class="confidence">({{ (message.intent.confidence * 100).toFixed(0) }}%)</span>
      </div>

      <div class="bubble" :class="message.isUser ? 'bubble-user' : 'bubble-bot'">
        <div class="message-text" v-html="formatContent(message.content)"></div>
      </div>

      <div class="message-time">
        {{ message.isUser ? '您' : '小E' }} / {{ formatTime(message.createdAt) }}
      </div>
    </div>

    <div v-if="message.isUser" class="avatar user-avatar">我</div>
  </div>
</template>

<script setup lang="ts">
import type { Message } from '@/types/chat'
import { formatTime } from '@/utils/formatTime'

defineProps<{
  message: Message
}>()

function formatContent(content: string): string {
  let html = content.replace(/\n/g, '<br>')
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
  html = html.replace(
    /(https?:\/\/[^\s<]+)/g,
    '<a href="$1" target="_blank" rel="noopener">$1</a>'
  )
  return html
}
</script>

<style scoped>
.message-bubble { display: flex; align-items: flex-start; margin-bottom: 20px; gap: 10px; max-width: 80%; }
.message-bubble.is-user { flex-direction: row-reverse; margin-left: auto; }

.avatar {
  width: 36px; height: 36px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 700; flex-shrink: 0;
}
.bot-avatar { background: linear-gradient(135deg, #667eea, #764ba2); color: #fff; }
.user-avatar { background: #e8eaed; color: #5f6368; }

.bubble-wrapper { display: flex; flex-direction: column; gap: 4px; min-width: 0; }
.message-bubble.is-user .bubble-wrapper { align-items: flex-end; }

.meta-tag { font-size: 10px; color: #909399; padding: 2px 6px; background: #f0f2f5; border-radius: 4px; }
.meta-tag .confidence { color: #67c23a; }

.bubble { padding: 10px 14px; border-radius: 14px; line-height: 1.6; word-break: break-word; }
.bubble-user {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff; border-bottom-right-radius: 4px;
}
.bubble-bot { background: #fff; color: #303133; border-bottom-left-radius: 4px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06); }

.message-text { font-size: 14px; }
.message-text :deep(a) { color: inherit; text-decoration: underline; }
.message-time { font-size: 10px; color: #c0c4cc; padding: 0 4px; }
</style>
