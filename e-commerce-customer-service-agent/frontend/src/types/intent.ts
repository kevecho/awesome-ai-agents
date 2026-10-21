export interface Entity {
  type: string
  value: string
  start: number
  end: number
}

export interface IntentResult {
  intent_code: string
  intent_name: string
  confidence: number
  entities: Entity[]
  handler_type: string
  priority: number
}

export interface IntentClassifyResponse {
  intent: IntentResult
  processing_time_ms: number
}
