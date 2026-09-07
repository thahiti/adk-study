"""모델 생성 공용 코드.

모든 단계는 이 모듈의 make_model 로만 모델을 만든다.
1.36.2에서 OpenAI 모델은 LiteLlm 을 통해서만 쓸 수 있다.
"""

import os

from dotenv import load_dotenv
from google.adk.models.lite_llm import LiteLlm

DEFAULT_MODEL = "gpt-4o-mini"


def make_model() -> LiteLlm:
    """.env 의 MODEL_NAME 으로 OpenAI 모델을 만든다.

    adk web 은 .env 를 먼저 읽지만 python -m 으로 실행하는
    스크립트는 그렇지 않으므로 여기서 load_dotenv 를 부른다.
    """
    load_dotenv()
    name = os.environ.get("MODEL_NAME", DEFAULT_MODEL)
    return LiteLlm(model=f"openai/{name}")
