import re

from pydantic import AliasChoices, BaseModel, Field, field_validator
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from .config import DEEPSEEK_API_KEY, DEEPSEEK_MODEL


class QuestionOutput(BaseModel):
    question_type: str = Field(default="single_choice", description="single_choice or true_false", validation_alias=AliasChoices("question_type", "type"))
    knowledge_point: str = Field(default="核心概念", validation_alias=AliasChoices("knowledge_point", "knowledgePoint"))
    difficulty: str = Field(default="beginner")
    stem: str = Field(default="", validation_alias=AliasChoices("stem", "question"))
    options: list[dict[str, str]] = Field(default_factory=list)
    answer: str = Field(default="A", validation_alias=AliasChoices("answer", "correct_answer", "correctAnswer"))
    explanation: str = ""

    @field_validator("options", mode="before")
    @classmethod
    def normalize_options(cls, value: object) -> list[dict[str, str]]:
        if not isinstance(value, list):
            return []
        normalized: list[dict[str, str]] = []
        for index, item in enumerate(value):
            if isinstance(item, dict):
                option_id = str(item.get("id", item.get("key", chr(65 + index))))
                text = str(item.get("text", item.get("content", "")))
            else:
                raw = str(item)
                match = re.match(r"^([A-D])(?:[.、:：)）\\s]+)(.+)$", raw)
                option_id = match.group(1) if match else chr(65 + index)
                text = match.group(2).strip() if match else raw
            normalized.append({"id": option_id, "text": text})
        return normalized


class DeepSeekQuestionChain:
    def __init__(self) -> None:
        if not DEEPSEEK_API_KEY:
            raise RuntimeError("DEEPSEEK_API_KEY is required for the real AI provider")
        model = ChatOpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com",
            model=DEEPSEEK_MODEL,
            temperature=0.2,
            timeout=30,
            max_retries=1,
        )
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是严谨的学习出题助手。请只输出一个合法 JSON 对象，不要输出 Markdown 或代码围栏。
主题：{topic}
难度：{difficulty}
题型：{question_type}
JSON 必须严格包含以下字段：
{{"question_type":"single_choice","knowledge_point":"具体知识点","difficulty":"beginner","stem":"具体问题","options":[{{"id":"A","text":"具体选项"}},{{"id":"B","text":"具体选项"}},{{"id":"C","text":"具体选项"}},{{"id":"D","text":"具体选项"}}],"answer":"A","explanation":"说明为什么该答案正确"}}
单选题必须提供 A、B、C、D 四个具体选项，判断题必须提供 A（正确）、B（错误）两个具体选项；answer 必须是正确选项 id，不能使用占位词或空字符串。"""),
            ("human", "请生成第 {index} 题。题目、每个选项、正确答案和解析都必须围绕主题给出具体内容。"),
        ])
        self.chain = prompt | model.with_structured_output(QuestionOutput, method="json_mode")

    def invoke(self, topic: str, difficulty: str, question_type: str, index: int) -> QuestionOutput:
        return self.chain.invoke({
            "topic": topic,
            "difficulty": difficulty,
            "question_type": question_type,
            "index": index,
        })
