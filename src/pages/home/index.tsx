import { useEffect, useState } from 'react'
import { Button, Input, Text, View } from '@tarojs/components'
import Taro from '@tarojs/taro'
import BottomNav from '../../components/BottomNav'
import { createSession, getSession } from '../../services/api'
import type { Difficulty } from '../../types/api'
import { getActiveSession, saveActiveSession } from '../../utils/storage'
import './index.scss'

export default function HomePage() {
  const [topic, setTopic] = useState('')
  const [questionCount, setQuestionCount] = useState<5 | 10>(5)
  const [difficulty, setDifficulty] = useState<Difficulty>('beginner')
  const [loading, setLoading] = useState(false)
  const [resumeId, setResumeId] = useState('')

  useEffect(() => {
    const sessionId = getActiveSession()
    if (sessionId) setResumeId(sessionId)
  }, [])

  const start = async () => {
    if (!topic.trim()) {
      Taro.showToast({ title: '先输入一个学习主题', icon: 'none' })
      return
    }
    setLoading(true)
    try {
      const session = await createSession(topic.trim(), questionCount, difficulty)
      saveActiveSession(session.sessionId)
      Taro.navigateTo({ url: `/pages/game/index?sessionId=${session.sessionId}` })
    } catch {
      Taro.showToast({ title: '航线生成失败，请重试', icon: 'none' })
    } finally {
      setLoading(false)
    }
  }

  const resume = async () => {
    setLoading(true)
    try {
      const session = await getSession(resumeId)
      if (session.status === 'completed') {
        Taro.navigateTo({ url: `/pages/report/index?sessionId=${resumeId}` })
      } else {
        Taro.navigateTo({ url: `/pages/game/index?sessionId=${resumeId}` })
      }
    } catch {
      Taro.showToast({ title: '找不到可恢复的练习', icon: 'none' })
    } finally {
      setLoading(false)
    }
  }

  return <View className="home-page">
    <View className="home-page__topbar"><Text>学习记录 · 09.11</Text><Text className="avatar">✦</Text></View>
    <View className="home-page__hero"><Text className="eyebrow">YOUR NEXT ADVENTURE</Text><Text className="hero-title">今天探索{`\n`}哪类知识主题？</Text><Text className="hero-copy">输入一个想弄懂的主题，AI 助教{`\n`}会为你生成一条专属学习路径。</Text></View>
    <View className="map-card"><Text className="map-card__title">新的学习路径</Text><View className="route"><Text className="node is-active">起</Text><Text className="route-line" /><Text className="node">2</Text><Text className="route-line" /><Text className="node">3</Text><Text className="route-line" /><Text className="node">终</Text></View></View>
    <View className="input-box"><Input value={topic} onInput={(event) => setTopic(event.detail.value)} placeholder="例如：用 5 题了解量子力学基础" maxlength={200} /></View>
    <View className="choice-row"><Text className={questionCount === 5 ? 'choice is-selected' : 'choice'} onClick={() => setQuestionCount(5)}>5 题</Text><Text className={questionCount === 10 ? 'choice is-selected' : 'choice'} onClick={() => setQuestionCount(10)}>10 题</Text><Text className="choice-label">难度</Text><Text className={difficulty === 'beginner' ? 'choice is-selected' : 'choice'} onClick={() => setDifficulty('beginner')}>入门</Text><Text className={difficulty === 'advanced' ? 'choice is-selected' : 'choice'} onClick={() => setDifficulty('advanced')}>进阶</Text><Text className={difficulty === 'expert' ? 'choice is-selected' : 'choice'} onClick={() => setDifficulty('expert')}>专家</Text></View>
    <Button className="primary-button" loading={loading} onClick={start}>开始练习　✦</Button>
    {resumeId && <Text className="resume-link" onClick={resume}>继续上次练习　→</Text>}
    <BottomNav active="home" />
  </View>
}
