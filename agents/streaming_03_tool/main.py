"""streaming_03_tool: 도구 호출 턴을 SSE 로 돌렸을 때의 이벤트 순서.

도구 호출은 조각으로 오지 않는다. function_call 과 function_response
가 먼저 non-partial 로 오고, 그 결과를 본 모델의 답만 조각으로 온다.

실행: uv run python -m agents.streaming_03_tool.main [메시지]
"""

import asyncio
import sys

from google.adk.agents import BaseAgent
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.events import Event
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from .agent import root_agent

# Runner 는 에이전트가 정의된 agents/ 아래 폴더 이름을 app_name 으로
# 기대한다. 다르면 경고 로그를 남기므로 폴더 이름과 같게 둔다.
APP_NAME = "streaming_03_tool"
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
    kind = "partial" if event.partial else "text"
    return f"[{event.author}] {kind} {text}"


async def run(
    agent: BaseAgent, text: str, *, streaming: bool = True
) -> list[Event]:
    """세션 하나를 만들고 메시지 한 개를 보내 이벤트를 출력하고 모은다.

    streaming 이 True 면 SSE 모드라 partial 이벤트가 조각으로 오고,
    False 면 NONE 모드라 최종 이벤트만 온다.
    """
    session_service = InMemorySessionService()
    runner = Runner(
        app_name=APP_NAME, agent=agent, session_service=session_service
    )
    session = await session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID
    )
    message = types.Content(
        role="user", parts=[types.Part.from_text(text=text)]
    )
    mode = StreamingMode.SSE if streaming else StreamingMode.NONE
    events: list[Event] = []
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=session.id,
        new_message=message,
        run_config=RunConfig(streaming_mode=mode),
    ):
        if event.partial:
            parts = event.content.parts if event.content else None
            print(parts[0].text if parts else "", end="", flush=True)
        else:
            print()
            print(describe(event))
        events.append(event)
    return events


if __name__ == "__main__":
    asyncio.run(
        run(
            root_agent,
            " ".join(sys.argv[1:]) or "안녕 하세요 글자 수 세 줘",
        )
    )
