import { View, Text } from '@tarojs/components'
import './index.scss'

type Props = { title: string; back?: boolean }

export default function TopBar({ title, back = false }: Props) {
  return <View className="topbar"><Text className="topbar__side">{back ? '‹' : '学习记录 · 09.11'}</Text><Text className="topbar__title">{title}</Text><Text className="topbar__avatar">✦</Text></View>
}
