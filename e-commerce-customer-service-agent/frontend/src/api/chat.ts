import request from '@/utils/request'
import type {
  CreateSessionResponse,
  SendMessageRequest,
  SendMessageResponse,
} from '@/types/chat'

export const chatApi = {
  createSession(userId?: number, channel = 'web') {
    return request.post<any, CreateSessionResponse>('/chat/session', {
      user_id: userId,
      channel,
    })
  },

  sendMessage(data: SendMessageRequest) {
    return request.post<any, SendMessageResponse>('/chat/send', {
      session_id: data.sessionId,
      content: data.content,
      user_id: data.userId,
      content_type: data.contentType || 'text',
    })
  },

  getHistory(sessionId: string, page = 1, pageSize = 20) {
    return request.get('/chat/history', {
      params: { session_id: sessionId, page, page_size: pageSize },
    })
  },

  transferToHuman(sessionId: string, reason?: string) {
    return request.post('/chat/transfer', {
      session_id: sessionId,
      reason: reason || 'user_requested',
    })
  },

  rateSession(sessionId: string, score: number, comment?: string) {
    return request.post('/chat/rate', {
      session_id: sessionId,
      score,
      comment,
    })
  },
}
