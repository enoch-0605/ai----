export type Difficulty = 'beginner' | 'advanced' | 'expert'
export type QuestionType = 'single_choice' | 'true_false'
export type SessionStatus = 'playing' | 'feedback' | 'completed' | 'failed'

export interface QuestionOption {
  id: string
  text: string
}

export interface PublicQuestion {
  questionId: string
  type: QuestionType
  knowledgePoint: string
  difficulty: Difficulty
  stem: string
  options: QuestionOption[]
}

export interface CreateSessionResponse {
  sessionId: string
  status: SessionStatus
  currentIndex: number
  totalQuestions: number
  score: number
  life: number
  question: PublicQuestion
}

export interface SessionResponse {
  sessionId: string
  status: SessionStatus
  currentIndex: number
  totalQuestions: number
  score: number
  life: number
  question?: PublicQuestion
  feedback?: QuestionFeedback
}

export interface QuestionFeedback {
  answer: string
  isCorrect: boolean
  explanation: string
  encouragement: string
}

export interface SubmitAnswerResponse {
  sessionId: string
  status: SessionStatus
  currentIndex: number
  totalQuestions: number
  score: number
  life: number
  feedback: QuestionFeedback
  nextQuestion?: PublicQuestion
}

export interface LearningReport {
  sessionId: string
  score: number
  totalQuestions: number
  accuracy: number
  summary: string
  strengths: string[]
  weaknesses: string[]
  recommendations: string[]
  disclaimer: string
}
