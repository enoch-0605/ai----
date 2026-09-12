import Taro from '@tarojs/taro'
import { getMe, login } from '../services/api'
import { clearAuthToken, getActiveSession, getAuthToken, saveAuthToken } from './storage'

export async function ensureAuth() {
  if (getAuthToken()) {
    try {
      await getMe()
      return
    } catch {
      clearAuthToken()
    }
  }
  const result = await Taro.login()
  const response = await login('wechat', result.code, getActiveSession() || undefined)
  saveAuthToken(response.token)
}
