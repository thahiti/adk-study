"""runner_02_services: 세션 서비스를 SQLite 로 바꾸고 다른 서비스도 넣는다.

Runner 는 세션, 아티팩트, 메모리 세 서비스를 받는다. 세션 서비스를
SqliteSessionService 로 바꾸면 스크립트를 다시 실행해도 같은
session_id 로 대화가 이어진다.

실행: uv run python -m agents.runner_02_services.main [메시지]
"""

import asyncio
import sys

from google.adk.agents import BaseAgent
from google.adk.artifacts import InMemoryArtifactService
from google.adk.events import Event
from google.adk.memory import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions.sqlite_session_service import SqliteSessionService
from google.genai import types

from .agent import root_agent

APP_NAME = "runner_02_services"
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


async def run(
    agent: BaseAgent,
    text: str,
    *,
    db_path: str = "sessions.db",
    session_id: str = "runner-demo",
) -> list[Event]:
    """SQLite 세션에 메시지 한 개를 보내 이벤트를 출력하고 모은다.

    같은 db_path 와 session_id 로 다시 부르면 이전 대화에 이어진다.
    """
    session_service = SqliteSessionService(f"sqlite:///{db_path}")
    runner = Runner(
        app_name=APP_NAME,
        agent=agent,
        session_service=session_service,
        artifact_service=InMemoryArtifactService(),
        memory_service=InMemoryMemoryService(),
    )
    session = await session_service.get_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=session_id
    )
    if session is None:
        session = await session_service.create_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=session_id
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
