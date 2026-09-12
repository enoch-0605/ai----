import Taro from '@tarojs/taro'
import type { CreateSessionResponse, Difficulty, LearningReport, SessionResponse, SubmitAnswerResponse } from '../types/api'

const API_BASE_URL = 'http://127.0.0.1:8000/api/v1'

async function request<T>(path: string, options: Omit<Taro.request.Option, 'url'> = {}): Promise<T> {
  const response = await Taro.request<T>({
    url: `${API_BASE_URL}${path}`,
    timeout: 30000,
    ...options,
  })
  if (response.statusCode < 200 || response.statusCode >= 300) {
    throw new Error(typeof response.data === 'object' && response.data && 'detail' in response.data ? String(response.data.detail) : 'REQUEST_FAILED')
  }
  return response.data
}

export function createSession(topic: string, questionCount: 5 | 10, difficulty: Difficulty) {
  return request<CreateSessionResponse>('/sessions', {
    method: 'POST',
    data: { topic, questionCount, difficulty, questionTypes: ['single_choice', 'true_false'] },
  })
}

export function getSession(sessionId: string) {
  return request<SessionResponse>(`/sessions/${sessionId}`)
}

export function submitAnswer(sessionId: string, questionId: string, answer: string, clientRequestId: string) {
  return request<SubmitAnswerResponse>(`/sessions/${sessionId}/answers`, {
    method: 'POST',
    data: { questionId, answer, clientRequestId },
  })
}

export function continueSession(sessionId: string) {
  return request<SessionResponse>(`/sessions/${sessionId}/continue`, { method: 'POST' })
}

export function getReport(sessionId: string) {
  return request<LearningReport>(`/sessions/${sessionId}/reports`, { method: 'POST' })
}
