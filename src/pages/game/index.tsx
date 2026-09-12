import { useEffect, useState } from 'react'
import { Button, Text, View } from '@tarojs/components'
import Taro, { useLoad } from '@tarojs/taro'
import TopBar from '../../components/TopBar'
import { continueSession, getSession, submitAnswer } from '../../services/api'
import type { PublicQuestion, QuestionFeedback, SessionStatus } from '../../types/api'
import { saveActiveSession } from '../../utils/storage'
import './index.scss'

export default function GamePage() {
  const [sessionId, setSessionId] = useState('')
  const [question, setQuestion] = useState<PublicQuestion>()
  const [feedback, setFeedback] = useState<QuestionFeedback>()
  const [status, setStatus] = useState<SessionStatus>('playing')
  const [index, setIndex] = useState(0)
  const [total, setTotal] = useState(5)
  const [score, setScore] = useState(0)
  const [life, setLife] = useState(3)
  const [selected, setSelected] = useState('')
  const [loading, setLoading] = useState(false)

  useLoad((params) => { if (params.sessionId) setSessionId(params.sessionId) })
  useEffect(() => { if (sessionId) loadSession(sessionId) }, [sessionId])

  const loadSession = async (id: string) => {
    try {
      const session = await getSession(id)
      setQuestion(session.question)
      setFeedback(session.feedback)
      setStatus(session.status)
      setIndex(session.currentIndex)
      setTotal(session.totalQuestions)
      setScore(session.score)
      setLife(session.life)
      saveActiveSession(id)
    } catch { Taro.showToast({ title: '加载练习失败，请重试', icon: 'none' }) }
  }

  const answer = async () => {
    if (!question || !selected || loading || status !== 'playing') return
    setLoading(true)
    try {
      const result = await submitAnswer(sessionId, question.questionId, selected, `${Date.now()}-${question.questionId}`)
      setFeedback(result.feedback)
      setStatus(result.status)
      setScore(result.score)
      setLife(result.life)
      setIndex(result.currentIndex)
      if (result.status === 'completed') {
        setTimeout(() => Taro.navigateTo({ url: `/pages/report/index?sessionId=${sessionId}` }), 600)
      }
    } catch { Taro.showToast({ title: '提交失败，请重试', icon: 'none' }) }
    finally { setLoading(false) }
  }

  const next = async () => {
    setLoading(true)
    try {
      const session = await continueSession(sessionId)
      setQuestion(session.question)
      setFeedback(undefined)
      setStatus(session.status)
      setIndex(session.currentIndex)
      setSelected('')
    } catch { Taro.showToast({ title: '下一题加载失败，请重试', icon: 'none' }) }
    finally { setLoading(false) }
  }

  if (!question) return <View className="game-page game-page--loading"><Text>正在生成第一题 · · ·</Text></View>
  const progress = `${Math.round(((index + (feedback ? 1 : 0)) / total) * 100)}%`
  return <View className="game-page"><TopBar title="当前练习" back /><View className="game-top"><View className="game-title"><Text>第 {index + 1} / {total} 题</Text><Text className="score">得分 {score}</Text></View><View className="progress"><View style={{ width: progress }} /></View><View className="stats"><Text>当前进度 · {question.difficulty === 'beginner' ? '入门' : question.difficulty === 'advanced' ? '进阶' : '专家'}难度</Text><Text className="life">{'♥ '.repeat(life)}{'♡ '.repeat(3 - life)}</Text></View></View><View className="question-card"><Text className="tag">{question.type === 'true_false' ? '判断题' : '单选题'} · {question.difficulty}</Text><Text className="question-stem">{question.stem}</Text></View><View className="options">{question.options.map((option) => <View key={option.id} className={`option ${selected === option.id ? 'is-selected' : ''} ${feedback ? (feedback.isCorrect && selected === option.id ? 'is-correct' : !feedback.isCorrect && selected === option.id ? 'is-wrong' : '') : ''}`} onClick={() => !feedback && setSelected(option.id)}><Text className="letter">{option.id}</Text><Text>{option.text}</Text></View>)}</View>{feedback ? <View className={`feedback ${feedback.isCorrect ? 'is-correct' : 'is-wrong'}`}><Text className="feedback-title">{feedback.isCorrect ? '回答正确 · 继续保持' : '再想一想 · 这次没有命中'}</Text><Text className="feedback-copy">{feedback.explanation}</Text><Text className="feedback-copy">{feedback.encouragement}</Text>{status !== 'completed' && <Button className="primary-button" loading={loading} onClick={next}>继续下一题　→</Button>}</View> : <View><Text className="hint">选择你的答案后，AI 助教会立即给出答题解析。</Text><Button className="primary-button" loading={loading} onClick={answer}>提交答案　↗</Button></View>}</View>
}
