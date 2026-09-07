"""loop_03_delegation: 자식 이벤트도 부모의 yield 를 거쳐 러너로 온다.

러너는 넘겨받은 에이전트 하나만 돌린다. 자식이 낸 이벤트는 부모가
다시 yield 해야 이 스크립트의 for 루프에 도착한다. 그래서 출력은
`runner: got 자식이 답함` 다음에 `agent: after child` 순서가 되고,
자식 이벤트가 부모와 러너를 차례로 거쳤다는 것을 눈으로 볼 수 있다.

실행: uv run python -m agents.loop_03_delegation.main
"""

import asyncio

from google.adk.agents import BaseAgent
from google.adk.events import Event
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from .agent import root_agent

APP_NAME = "loop_03_delegation"
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
        # 자식 이벤트라면 자식과 부모가 둘 다 멈춰 있다. 부모는
        # 자식을 감싼 async for 안에서 기다리는 중이다.
        print(f"runner: got {text_of(event)}")
        events.append(event)
    return events


if __name__ == "__main__":
    asyncio.run(run(root_agent, "시작"))
