export interface Entity {
  type: string
  value: string
}

export interface IntentInfo {
  intent_code: string
  intent_name: string
  confidence: number
  entities: Entity[]
  handler_type: string
  priority: number
}

export type SentimentType = 'positive' | 'neutral' | 'negative'
export type SenderType = 'user' | 'bot' | 'agent'

export interface Message {
  id: string
  sessionId: string
  senderType: SenderType
  content: string
  contentType: string
  createdAt: string
  isUser: boolean
  intent?: IntentInfo
  sentiment?: SentimentType
  sentimentScore?: number
  isHumanTransfer?: boolean
  metadata?: Record<string, unknown>
}

export interface SessionInfo {
  sessionId: string
  userId: number | null
  status: string
  channel: string
  startedAt?: string
  messageCount: number
  botName: string
}

export interface SendMessageRequest {
  sessionId: string
  content: string
  userId?: number
  contentType?: string
}

export interface SendMessageResponse {
  response: string
  intent: IntentInfo
  sentiment: SentimentType
  sentiment_score: number
  quick_replies: string[]
  need_transfer: boolean
}

export interface CreateSessionResponse {
  session: SessionInfo
  welcome_message: string
  quick_replies: string[]
}

export interface QuickService {
  code: string
  name: string
  text: string
}
