import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { chatApi } from '@/api/chat'
import type { Message, SessionInfo, SentimentType } from '@/types/chat'

export const useChatStore = defineStore('chat', () => {
  const messages = ref<Message[]>([])
  const sessionInfo = ref<SessionInfo | null>(null)
  const currentSentiment = ref<SentimentType | null>(null)
  const sentimentScore = ref(0)
  const quickReplies = ref<string[]>([])
  const isConnected = ref(false)
  const isTyping = ref(false)

  const lastMessage = computed(() =>
    messages.value.length > 0 ? messages.value[messages.value.length - 1] : null
  )

  const messageCount = computed(() => messages.value.length)

  async function initSession(): Promise<void> {
    try {
      const result = await chatApi.createSession()
      sessionInfo.value = {
        sessionId: result.session.session_id,
        userId: result.session.user_id,
        status: result.session.status,
        channel: result.session.channel,
        messageCount: 0,
        botName: result.session.bot_name,
      }
      isConnected.value = true

      // Add welcome message
      messages.value.push({
        id: 'welcome',
        sessionId: result.session.session_id,
        senderType: 'bot',
        content: result.welcome_message,
        contentType: 'text',
        createdAt: new Date().toISOString(),
        isUser: false,
      })

      quickReplies.value = result.quick_replies
    } catch (error) {
      console.error('Failed to initialize session:', error)
    }
  }

  async function sendMessage(content: string): Promise<void> {
    if (!sessionInfo.value) return

    // Add user message
    const userMsg: Message = {
      id: `user-${Date.now()}`,
      sessionId: sessionInfo.value.sessionId,
      senderType: 'user',
      content,
      contentType: 'text',
      createdAt: new Date().toISOString(),
      isUser: true,
    }
    messages.value.push(userMsg)
    quickReplies.value = []
    isTyping.value = true

    try {
      const result = await chatApi.sendMessage({
        sessionId: sessionInfo.value.sessionId,
        content,
        userId: sessionInfo.value.userId ?? undefined,
      })

      // Add bot response
      const botMsg: Message = {
        id: `bot-${Date.now()}`,
        sessionId: sessionInfo.value.sessionId,
        senderType: 'bot',
        content: result.response,
        contentType: 'text',
        createdAt: new Date().toISOString(),
        isUser: false,
        intent: result.intent,
        sentiment: result.sentiment,
        sentimentScore: result.sentiment_score,
      }
      messages.value.push(botMsg)

      currentSentiment.value = result.sentiment
      sentimentScore.value = result.sentiment_score

      if (result.quick_replies && result.quick_replies.length > 0) {
        quickReplies.value = result.quick_replies
      }
    } catch (error) {
      console.error('Failed to send message:', error)
      // Add error message
      messages.value.push({
        id: `error-${Date.now()}`,
        sessionId: sessionInfo.value.sessionId,
        senderType: 'bot',
        content: 'Sorry, I encountered an error. Please try again.',
        contentType: 'text',
        createdAt: new Date().toISOString(),
        isUser: false,
      })
    } finally {
      isTyping.value = false
    }
  }

  function resetSession(): void {
    messages.value = []
    sessionInfo.value = null
    currentSentiment.value = null
    sentimentScore.value = 0
    quickReplies.value = []
    isConnected.value = false
    isTyping.value = false
  }

  return {
    messages,
    sessionInfo,
    currentSentiment,
    sentimentScore,
    quickReplies,
    isConnected,
    isTyping,
    lastMessage,
    messageCount,
    initSession,
    sendMessage,
    resetSession,
  }
})
