export interface AgentStep {
  step_number: number
  thought: string
  action: string | null
  action_input: Record<string, unknown> | null
  observation: string | null
}

export interface AgentExecuteResponse {
  agent_id: string
  session_id: string
  final_answer: string
  steps: AgentStep[]
  tools_used: string[]
  execution_time_ms: number
}

export interface ToolInfo {
  name: string
  description: string
  requires_auth: boolean
  schema: Record<string, unknown>
}
