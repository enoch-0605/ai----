from app.ai_langchain import QuestionOutput


def test_question_output_normalizes_common_deepseek_shape():
    output = QuestionOutput.model_validate(
        {
            "type": "single_choice",
            "question": "RAG 中检索器的作用是什么？",
            "options": [
                "A. 检索相关文档",
                "B. 直接生成答案",
            ],
            "correct_answer": "A",
            "explanation": "检索器负责从知识库获取相关内容。",
        }
    )

    assert output.question_type == "single_choice"
    assert output.stem.startswith("RAG")
    assert output.options == [
        {"id": "A", "text": "检索相关文档"},
        {"id": "B", "text": "直接生成答案"},
    ]
    assert output.answer == "A"
