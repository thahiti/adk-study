"""loop_01_pause_resume: yield 가 러너로 제어를 넘기고 다시 받는 지점.

에이전트는 yield 앞뒤에 한 줄씩 찍고, 러너 쪽 for 루프는 이벤트를
받을 때마다 한 줄 찍는다. 두 출력이 번갈아 나오는 것이 이 단계의
전부다. 에이전트 코드는 이벤트를 한꺼번에 만들어 돌려주는 것이
아니라 하나 내보낼 때마다 멈췄다가 러너가 다음 것을 요청할 때
이어서 돈다.

adk web 은 이 파일을 부르지 않는다. 에이전트 로더가 읽는 것은
agent.py 뿐이라 러너 쪽 print 는 스크립트로 돌릴 때만 보인다.

실행: uv run python -m agents.loop_01_pause_resume.main
"""

import asyncio

from google.adk.agents import BaseAgent
from google.adk.events import Event
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from .agent import root_agent

APP_NAME = "loop_01_pause_resume"
USER_ID = "user"


def text_of(event: Event) -> str:
    """이벤트의 첫 텍스트 파트를 돌려준다. 없으면 빈 문자열이다."""
    parts = event.content.parts if event.content else None
    return (parts[0].text or "") if parts else ""


async def run(agent: BaseAgent, text: str) -> list[Event]:
    """메시지 한 개를 보내고 이벤트를 받을 때마다 한 줄 찍는다.

    공용 도우미 run_turn 은 이벤트를 리스트로 모아 주기만 해서
    하나하나 받는 시점이 보이지 않는다. 그 시점을 찍으려고 여기서는
    러너를 직접 만들어 async for 를 손으로 돈다.
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
    events: list[Event] = []
    async for event in runner.run_async(
        user_id=USER_ID, session_id=session.id, new_message=message
    ):
        # 이 줄이 찍히는 시점에 에이전트는 yield 에서 멈춰 있다.
        # 에이전트와 이 루프 사이에는 BaseAgent.run_async 와 러너의
        # _exec_with_plugin 을 포함해 생성자가 여러 겹 있지만 모두
        # 받은 이벤트를 그대로 다시 yield 하기만 한다. 버퍼가 없으니
        # 에이전트 한 줄과 이 한 줄이 번갈아 나온다.
        print(f"runner: got {text_of(event)}")
        events.append(event)
    return events


if __name__ == "__main__":
    asyncio.run(run(root_agent, "시작"))
