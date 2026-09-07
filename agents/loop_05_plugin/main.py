"""loop_05_plugin: 전환 뒤 다음 턴은 자식이 바로 이어받는다.

러너는 턴을 시작할 때 세션의 마지막 에이전트 이벤트 author 를 보고
실행할 에이전트를 고른다. 첫 턴에서 부모가 자식에게 넘겼다면 둘째
턴은 부모를 거치지 않고 자식이 바로 받는다.

실행: uv run python -m agents.loop_05_plugin.main
"""

import asyncio

from google.adk.agents import BaseAgent
from google.adk.events import Event
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from .agent import root_agent

APP_NAME = "loop_05_plugin"
USER_ID = "user"


async def run_turns(agent: BaseAgent, texts: list[str]) -> list[list[Event]]:
    """한 세션에 메시지를 차례로 보내고 턴마다 author 목록을 찍는다."""
    session_service = InMemorySessionService()
    runner = Runner(
        app_name=APP_NAME, agent=agent, session_service=session_service
    )
    session = await session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID
    )
    turns: list[list[Event]] = []
    for number, text in enumerate(texts, start=1):
        message = types.Content(
            role="user", parts=[types.Part.from_text(text=text)]
        )
        events = [
            event
            async for event in runner.run_async(
                user_id=USER_ID, session_id=session.id, new_message=message
            )
        ]
        authors = ", ".join(e.author for e in events)
        print(f"turn {number}: {authors}")
        turns.append(events)
    return turns


if __name__ == "__main__":
    asyncio.run(run_turns(root_agent, ["넘겨 줘", "하나 더 물어볼게"]))
