import { useEffect, useState } from 'react'
import { Button, Text, View } from '@tarojs/components'
import Taro from '@tarojs/taro'
import BottomNav from '../../components/BottomNav'
import { getHistory, getLearningOverview, getMistakes } from '../../services/api'
import type { HistoryItem, LearningOverview, MistakeItem } from '../../types/api'
import { ensureAuth } from '../../utils/auth'
import './index.scss'

export default function AssetsPage() {
  const [overview, setOverview] = useState<LearningOverview>()
  const [history, setHistory] = useState<HistoryItem[]>([])
  const [mistakes, setMistakes] = useState<MistakeItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.resolve().then(async () => {
      try {
        await ensureAuth()
        const [nextOverview, nextHistory, nextMistakes] = await Promise.all([getLearningOverview(), getHistory(), getMistakes()])
        setOverview(nextOverview)
        setHistory(nextHistory)
        setMistakes(nextMistakes)
      } catch (error) {
        const message = error instanceof Error ? error.message : '登录失败'
        Taro.showModal({ title: '微信登录失败', content: message, showCancel: false })
      } finally {
        setLoading(false)
      }
    })
  }, [])

  if (loading) return <View className="assets-page assets-page--loading"><Text>正在整理你的学习航海日志 · · ·</Text></View>
  return <View className="assets-page">
    <View className="assets-topbar"><Text>你的学习进度</Text><Text className="avatar">✦</Text></View>
    <View className="assets-hero"><Text className="eyebrow">LEARNING LOG</Text><Text className="assets-title">每一次练习{`\n`}都会留下进步。</Text><Text className="assets-copy">继续未完成的练习，或者回看曾经发现的知识岛屿。</Text></View>
    <View className="stats">
      <View><Text>{overview?.completedCount || 0}</Text><Text>完成练习</Text></View>
      <View><Text>{overview?.averageAccuracy || 0}%</Text><Text>平均正确率</Text></View>
      <View><Text>{overview?.totalMinutes || 0}m</Text><Text>学习时长</Text></View>
    </View>
    <Text className="section-title">最近练习</Text>
    {history.length === 0 && <Text className="empty">完成第一次练习后，记录会出现在这里。</Text>}
    {history.slice(0, 5).map((item) => <View className="history-item" key={item.sessionId} onClick={() => Taro.navigateTo({ url: `/pages/report/index?sessionId=${item.sessionId}` })}><View><Text className="history-topic">{item.topic}</Text><Text className="history-meta">{item.status === 'completed' ? '已完成' : '进行中'} · {item.accuracy}%</Text></View><Text className="history-score">{item.accuracy}%</Text></View>)}
    <View className="mistake-head"><Text className="section-title">错题宝藏</Text><Text>{mistakes.length} 个待复习</Text></View>
    {mistakes.slice(0, 3).map((item) => <View className="mistake-item" key={`${item.sessionId}-${item.questionId}`}><Text className="mistake-topic">{item.knowledgePoint}</Text><Text className="mistake-reason">错误原因：{item.reason}</Text><Text className="mistake-meta">{item.topic} · {item.difficulty === 'beginner' ? '入门' : item.difficulty === 'advanced' ? '进阶' : '专家'}</Text></View>)}
    {mistakes.length > 0 && <Button className="primary-button" onClick={() => Taro.showToast({ title: '错题专关即将开放', icon: 'none' })}>生成错题专关　✦</Button>}
    <BottomNav active="assets" />
  </View>
}
