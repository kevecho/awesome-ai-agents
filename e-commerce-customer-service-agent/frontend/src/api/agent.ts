import request from '@/utils/request'
import type { AgentExecuteResponse, ToolInfo } from '@/types/agent'

export const agentApi = {
  execute(sessionId: string, task: string, userId?: number) {
    return request.post<any, AgentExecuteResponse>('/agent/execute', {
      session_id: sessionId,
      user_id: userId,
      task,
    })
  },

  listTools() {
    return request.get<any, ToolInfo[]>('/agent/tools')
  },
}
