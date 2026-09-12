import { useEffect, useState } from 'react'
import { Button, Text, View } from '@tarojs/components'
import Taro, { useLoad } from '@tarojs/taro'
import BottomNav from '../../components/BottomNav'
import { getReport } from '../../services/api'
import type { LearningReport } from '../../types/api'
import './index.scss'

export default function ReportPage() {
  const [sessionId, setSessionId] = useState('')
  const [report, setReport] = useState<LearningReport>()
  const [loading, setLoading] = useState(true)
  useLoad((params) => { if (params.sessionId) setSessionId(params.sessionId) })
  useEffect(() => { if (sessionId) loadReport() }, [sessionId])

  const loadReport = async () => {
    try { setReport(await getReport(sessionId)) }
    catch { Taro.showToast({ title: '报告生成失败，请重试', icon: 'none' }) }
    finally { setLoading(false) }
  }

  if (loading || !report) return <View className="report-page report-page--loading"><Text>正在整理你的学习报告 · · ·</Text></View>
  return <View className="report-page"><View className="report-topbar"><Text onClick={() => Taro.navigateBack()}>‹</Text><Text>本次学习报告</Text><Text className="avatar">✦</Text></View><View className="report-hero"><Text className="eyebrow">SESSION COMPLETE</Text><Text className="report-title">练习完成！</Text><Text className="bounty">{report.score} / {report.totalQuestions}<Text> 学习得分</Text></Text><Text className="seal">AI 生成 · 学习参考</Text></View><View className="report-grid"><View><Text>{report.accuracy}%</Text><Text>正确率</Text></View><View><Text>{report.totalQuestions}</Text><Text>完成题数</Text></View></View><View className="report-content"><Text className="section-title">你的知识掌握图</Text><Text className="summary">{report.summary}</Text><View className="meter"><View style={{ width: `${report.accuracy}%` }} /></View><View className="pills"><Text>强项 · {report.strengths[0]}</Text><Text>待复习 · {report.weaknesses[0]}</Text></View><Text className="section-title">下一步建议</Text>{report.recommendations.map((recommendation) => <Text className="recommendation" key={recommendation}>✦ {recommendation}</Text>)}</View><Button className="primary-button" onClick={() => Taro.navigateTo({ url: '/pages/home/index' })}>开始新的练习　✦</Button><Text className="disclaimer">{report.disclaimer}</Text><BottomNav active="assets" /></View>
}
