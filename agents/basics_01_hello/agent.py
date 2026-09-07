"""basics_01_hello: instruction 만 있는 최소 LlmAgent.

adk web 은 agents/<폴더>/agent.py 안의 root_agent 변수를 찾아
에이전트로 띄운다. 이 이름은 ADK 로더가 정한 약속이라 바꿀 수 없다.
"""

from google.adk.agents import LlmAgent

from adk_study.models import make_model

root_agent = LlmAgent(
    # 유일한 필수 필드다. Python 식별자여야 하고, 이 에이전트가
    # 만든 이벤트의 author 가 되어 adk web Events 탭에 그대로 보인다.
    name="hello",
    # 비우면 ADK 기본값(gemini-2.5-flash)을 쓴다. 이 프로젝트는
    # OpenAI 모델을 쓰므로 .env 의 MODEL_NAME 으로 LiteLlm 을 만든다.
    # 문자열 대신 BaseLlm 객체를 넣을 수 있어 테스트에서는
    # 이 자리에 가짜 모델을 대입한다.
    model=make_model(),
    # 장식이 아니다. ADK 가 "The description about you is ..." 문장으로
    # 시스템 프롬프트에 넣고, 뒤 단계에서 부모 에이전트가 어느
    # 자식에게 넘길지 고를 때도 이 문장을 읽는다.
    description="인사만 하는 최소 에이전트",
    # 모델 요청의 system_instruction 이 된다. 매 턴 다시 보내므로
    # 세션에 저장되지 않고, 이벤트로도 남지 않는다.
    instruction="사용자에게 한국어로 짧고 친절하게 인사한다.",
)
