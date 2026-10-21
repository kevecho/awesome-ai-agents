import request from '@/utils/request'
import type { IntentClassifyResponse } from '@/types/intent'

export const intentApi = {
  classify(text: string, userId?: number) {
    return request.post<any, IntentClassifyResponse>('/intent/classify', {
      text,
      user_id: userId,
    })
  },

  classifyBatch(texts: string[]) {
    return request.post('/intent/classify-batch', { texts })
  },
}
