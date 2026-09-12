import { View, Text } from '@tarojs/components'
import Taro from '@tarojs/taro'
import './index.scss'

type Props = { active: 'home' | 'assets' | 'mine' }

export default function BottomNav({ active }: Props) {
  const goHome = () => Taro.switchTab({ url: '/pages/home/index' }).catch(() => Taro.navigateTo({ url: '/pages/home/index' }))
  return <View className="bottom-nav">
    <View className={`bottom-nav__item ${active === 'home' ? 'is-active' : ''}`} onClick={goHome}><Text>⌂</Text><Text>学习首页</Text></View>
    <View className={`bottom-nav__item ${active === 'assets' ? 'is-active' : ''}`}><Text>◈</Text><Text>学习资产</Text></View>
    <View className={`bottom-nav__item ${active === 'mine' ? 'is-active' : ''}`}><Text>◉</Text><Text>个人中心</Text></View>
  </View>
}
