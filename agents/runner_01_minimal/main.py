"""runner_01_minimal: Runner 를 직접 만들어 for 루프에서 이벤트를 받는다.

adk web 이 대신 해 주던 일을 스크립트로 옮긴다. 세션 서비스를 만들고,
Runner 에 에이전트와 서비스를 넣고, 세션을 만든 뒤, run_async 가
yield 하는 이벤트를 하나씩 받는다.

실행: uv run python -m agents.runner_01_minimal.main [메시지]

python -m 으로 실행하는 이유는 이 파일이 agents.runner_01_minimal
패키지의 모듈이기 때문이다. 파일 경로로 실행하면 `from .agent` 같은
상대 import 가 깨진다.
"""

import asyncio
import sys

from google.adk.agents import BaseAgent
from google.adk.events import Event
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from .agent import root_agent

# Runner 는 에이전트가 정의된 agents/ 아래 폴더 이름을 app_name 으로
# 기대한다. 다르면 경고 로그를 남기므로 폴더 이름과 같게 둔다.
APP_NAME = "runner_01_minimal"
USER_ID = "user"


def describe(event: Event) -> str:
    """이벤트를 한 줄로 요약한다. author 와 종류, 내용 순서다.

    도구 턴의 이벤트 셋은 parts 의 종류로 구분한다. function_call 과
    function_response 를 먼저 살피고, 둘 다 없으면 텍스트로 본다.
    이 단계는 도구를 한 번에 하나만 부르므로 첫 번째 것만 본다.
    """
    if event.get_function_calls():
        call = event.get_function_calls()[0]
        return f"[{event.author}] function_call {call.name} {call.args}"
    if event.get_function_responses():
        response = event.get_function_responses()[0].response
        return f"[{event.author}] function_response {response}"
    # content 가 None 인 이벤트도 있어서 바로 parts 를 읽지 않는다.
    parts = event.content.parts if event.content else None
    text = parts[0].text if parts else ""
    return f"[{event.author}] text {text}"


async def run(agent: BaseAgent, text: str) -> list[Event]:
    """세션 하나를 만들고 메시지 한 개를 보내 이벤트를 출력하고 모은다.

    테스트가 FakeLlm 을 끼운 에이전트로 이 함수를 부르므로 root_agent 를
    직접 쓰지 않고 인자로 받는다.
    """
    # session_service 는 Runner 의 필수 인자다. 대화 기록을 어디에
    # 둘지 Runner 가 정하지 않고 밖에서 받는다.
    session_service = InMemorySessionService()
    runner = Runner(
        app_name=APP_NAME, agent=agent, session_service=session_service
    )
    # 세션은 Runner 가 아니라 session_service 가 만든다. 미리 만들지
    # 않으면 run_async 가 SessionNotFoundError 를 낸다.
    session = await session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID
    )
    # 사용자 입력은 문자열이 아니라 genai Content 로 넘긴다.
    message = types.Content(
        role="user", parts=[types.Part.from_text(text=text)]
    )
    events: list[Event] = []
    # run_async 는 async generator 라 이벤트를 하나 꺼낼 때마다
    # 에이전트가 다음 yield 까지만 진행된다. 루프에 오는 이벤트는
    # 이미 세션에 저장된 뒤다.
    async for event in runner.run_async(
        user_id=USER_ID, session_id=session.id, new_message=message
    ):
        print(describe(event))
        events.append(event)
    return events


# 테스트가 이 모듈을 import 할 때는 실행되지 않도록 막는다.
# run 은 코루틴이라 asyncio.run 으로 이벤트 루프를 열어 돌린다.
if __name__ == "__main__":
    asyncio.run(
        run(root_agent, " ".join(sys.argv[1:]) or "안녕 하세요 글자 수 세 줘")
    )
