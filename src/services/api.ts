import Taro from '@tarojs/taro'
import type {
  CreateSessionResponse,
  Difficulty,
  HistoryItem,
  LearningOverview,
  LearningReport,
  LoginResponse,
  MistakeItem,
  SessionResponse,
  SubmitAnswerResponse,
  UserProfile,
} from '../types/api'
import { getAuthToken } from '../utils/storage'

const API_BASE_URL = 'http://192.168.101.97:8000/api/v1'

async function request<T>(path: string, options: Omit<Taro.request.Option, 'url'> = {}): Promise<T> {
  const token = getAuthToken()
  const response = await Taro.request<T>({
    url: `${API_BASE_URL}${path}`,
    timeout: 30000,
    ...options,
    header: {
      ...(options.header || {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  })
  if (response.statusCode < 200 || response.statusCode >= 300) {
    throw new Error(typeof response.data === 'object' && response.data && 'detail' in response.data ? String(response.data.detail) : 'REQUEST_FAILED')
  }
  return response.data
}

export function login(provider: 'mock' | 'wechat', code: string, anonymousSessionId?: string) {
  return request<LoginResponse>('/auth/login', { method: 'POST', data: { provider, code, anonymousSessionId } })
}

export function getMe() { return request<UserProfile>('/auth/me') }
export function getLearningOverview() { return request<LearningOverview>('/assets/overview') }
export function getHistory() { return request<HistoryItem[]>('/assets/history') }
export function getMistakes() { return request<MistakeItem[]>('/assets/mistakes') }

export function createSession(topic: string, questionCount: 5 | 10, difficulty: Difficulty) {
  return request<CreateSessionResponse>('/sessions', {
    method: 'POST',
    data: { topic, questionCount, difficulty, questionTypes: ['single_choice', 'true_false'] },
  })
}

export function getSession(sessionId: string) { return request<SessionResponse>(`/sessions/${sessionId}`) }

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
