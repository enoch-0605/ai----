import Taro from '@tarojs/taro'

const SESSION_KEY = 'zhiguan_active_session'
const AUTH_TOKEN_KEY = 'zhiguan_auth_token'

export function saveActiveSession(sessionId: string) {
  Taro.setStorageSync(SESSION_KEY, sessionId)
}

export function getActiveSession() {
  return Taro.getStorageSync<string>(SESSION_KEY) || ''
}

export function clearActiveSession() {
  Taro.removeStorageSync(SESSION_KEY)
}

export function saveAuthToken(token: string) {
  Taro.setStorageSync(AUTH_TOKEN_KEY, token)
}

export function getAuthToken() {
  return Taro.getStorageSync<string>(AUTH_TOKEN_KEY) || ''
}

export function clearAuthToken() {
  Taro.removeStorageSync(AUTH_TOKEN_KEY)
}
