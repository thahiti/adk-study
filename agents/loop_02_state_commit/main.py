"""loop_02_state_commit: yield 가 러너로 제어를 넘기고 다시 받는 지점.

에이전트는 yield 앞뒤에 한 줄씩 찍고, 러너 쪽 for 루프는 이벤트를
받을 때마다 한 줄 찍는다. 두 출력이 번갈아 나오는 것이 이 단계의
전부다. 에이전트 코드는 이벤트를 한꺼번에 만들어 돌려주는 것이
아니라 하나 내보낼 때마다 멈췄다가 러너가 다음 것을 요청할 때
이어서 돈다.

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
        # 이 줄이 찍히는 시점에 에이전트는 yield 에서 멈춰 있다.
        print(f"runner: got {text_of(event)}")
        events.append(event)
    return events


if __name__ == "__main__":
    asyncio.run(run(root_agent, "시작"))
