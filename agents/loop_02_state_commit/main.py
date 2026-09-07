"""loop_02_state_commit: yield 뒤에 state_delta 가 세션에 반영되어 있다.

loop_01_pause_resume 과 같은 러너 스크립트다. 달라진 것은 에이전트
쪽 출력뿐이라, 여기서는 announced 를 찍는 두 줄 사이에 러너 쪽
"runner: got 두 번째 알림" 이 끼어드는 것을 본다. 러너는 이벤트를
저장한 뒤에 호출자에게 넘기므로, 그 줄이 찍힌 시점에는 delta 가
이미 세션에 합쳐져 있다.

실행: uv run python -m agents.loop_02_state_commit.main
"""

import asyncio

from google.adk.agents import BaseAgent
from google.adk.events import Event
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from .agent import root_agent

APP_NAME = "loop_02_state_commit"
USER_ID = "user"


def text_of(event: Event) -> str:
    """이벤트의 첫 텍스트 파트를 돌려준다. 없으면 빈 문자열이다."""
    parts = event.content.parts if event.content else None
    return (parts[0].text or "") if parts else ""


async def run(agent: BaseAgent, text: str) -> list[Event]:
    """메시지 한 개를 보내고 이벤트를 받을 때마다 한 줄 찍는다."""
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
        # 이 줄이 찍히는 시점에 에이전트는 yield 에서 멈춰 있고,
        # 러너는 이미 append_event 를 끝냈다. 러너 안에서 저장이
        # yield 보다 앞에 있어서, 호출자가 이벤트를 보기 전에 세션
        # 반영이 끝난다.
        print(f"runner: got {text_of(event)}")
        events.append(event)
    return events


if __name__ == "__main__":
    asyncio.run(run(root_agent, "시작"))
