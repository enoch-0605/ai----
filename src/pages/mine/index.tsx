import { useEffect, useState } from 'react'
import { Button, Text, View } from '@tarojs/components'
import Taro from '@tarojs/taro'
import BottomNav from '../../components/BottomNav'
import { getMe } from '../../services/api'
import type { UserProfile } from '../../types/api'
import { clearAuthToken, getAuthToken } from '../../utils/storage'
import { ensureAuth } from '../../utils/auth'
import './index.scss'

export default function MinePage() {
  const [user, setUser] = useState<UserProfile>()
  useEffect(() => {
    Promise.resolve().then(async () => {
      try {
        await ensureAuth()
        if (getAuthToken()) setUser(await getMe())
      } catch (error) {
        const message = error instanceof Error ? error.message : '登录失败'
        Taro.showModal({ title: '微信登录失败', content: message, showCancel: false })
      }
    })
  }, [])

  const logout = () => {
    clearAuthToken()
    setUser(undefined)
    Taro.showToast({ title: '已退出登录', icon: 'none' })
  }

  return <View className="mine-page">
    <View className="mine-topbar"><Text>个人中心</Text><Text className="avatar">◉</Text></View>
    <View className="profile"><View className="profile-avatar">{user?.nickname.slice(0, 1) || '学'}</View><View><Text className="profile-name">{user?.nickname || '学习用户'}</Text><Text className="profile-caption">把好奇心，变成完成练习的风。</Text></View></View>
    <View className="mine-card"><Text className="eyebrow">ACCOUNT</Text><Text className="mine-title">你的学习身份</Text><Text className="mine-copy">登录后，练习记录和错题会跟随你的账号，在设备之间保持连续。</Text></View>
    <View className="mine-row"><Text>学习记录</Text><Text onClick={() => Taro.navigateTo({ url: '/pages/assets/index' })}>查看 →</Text></View>
    <View className="mine-row"><Text>登录状态</Text><Text className="status">{user ? '已登录' : '未登录'}</Text></View>
    <Button className="logout-button" onClick={logout}>退出登录</Button>
    <Text className="disclaimer">AI 生成内容仅供学习参考。</Text>
    <BottomNav active="mine" />
  </View>
}
