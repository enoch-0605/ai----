import Taro from '@tarojs/taro'

const SESSION_KEY = 'zhiguan_active_session'

export function saveActiveSession(sessionId: string) {
  Taro.setStorageSync(SESSION_KEY, sessionId)
}

export function getActiveSession() {
  return Taro.getStorageSync<string>(SESSION_KEY) || ''
}

export function clearActiveSession() {
  Taro.removeStorageSync(SESSION_KEY)
}
