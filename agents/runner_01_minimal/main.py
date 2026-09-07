"""runner_01_minimal: Runner 를 직접 만들어 for 루프에서 이벤트를 받는다.

adk web 이 대신 해 주던 일을 스크립트로 옮긴다. 세션 서비스를 만들고,
Runner 에 에이전트와 서비스를 넣고, 세션을 만든 뒤, run_async 가
yield 하는 이벤트를 하나씩 받는다.

실행: uv run python -m agents.runner_01_minimal.main [메시지]
"""

import asyncio
import sys

from google.adk.agents import BaseAgent
from google.adk.events import Event
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from .agent import root_agent

APP_NAME = "runner_01_minimal"
USER_ID = "user"


def describe(event: Event) -> str:
    """이벤트를 한 줄로 요약한다. author 와 종류, 내용 순서다."""
    if event.get_function_calls():
        call = event.get_function_calls()[0]
        return f"[{event.author}] function_call {call.name} {call.args}"
    if event.get_function_responses():
        response = event.get_function_responses()[0].response
        return f"[{event.author}] function_response {response}"
    parts = event.content.parts if event.content else None
    text = parts[0].text if parts else ""
    return f"[{event.author}] text {text}"


async def run(agent: BaseAgent, text: str) -> list[Event]:
    """세션 하나를 만들고 메시지 한 개를 보내 이벤트를 출력하고 모은다."""
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
    events: list[Event] = []
    async for event in runner.run_async(
        user_id=USER_ID, session_id=session.id, new_message=message
    ):
        print(describe(event))
        events.append(event)
    return events


if __name__ == "__main__":
    asyncio.run(
        run(root_agent, " ".join(sys.argv[1:]) or "안녕 하세요 글자 수 세 줘")
    )
