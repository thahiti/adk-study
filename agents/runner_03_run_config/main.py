"""runner_03_run_config: RunConfig 와 state_delta 로 한 턴을 조정한다.

run_async 는 메시지 외에 두 가지를 더 받는다. run_config 는 이 턴의
실행 제한이고, state_delta 는 에이전트가 돌기 전에 세션 state 에
반영할 값이다.

실행: uv run python -m agents.runner_03_run_config.main [메시지]
"""

import asyncio
import sys
from typing import Any

from google.adk.agents import BaseAgent
from google.adk.agents.run_config import RunConfig
from google.adk.artifacts import InMemoryArtifactService
from google.adk.events import Event
from google.adk.memory import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions.sqlite_session_service import SqliteSessionService
from google.genai import types

from .agent import root_agent

APP_NAME = "runner_03_run_config"
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
    max_llm_calls: int = 4,
    state: dict[str, Any] | None = None,
) -> list[Event]:
    """SQLite 세션에 메시지 한 개를 보내 이벤트를 출력하고 모은다.

    max_llm_calls 는 한 턴의 모델 호출 상한이다. state 는 에이전트가
    돌기 전에 세션 state 에 반영할 값이다.

    Raises:
        LlmCallsLimitExceededError: 모델 호출이 max_llm_calls 를 넘으려
            할 때. 그때까지 출력한 이벤트는 세션에 이미 저장돼 있고,
            예외는 잡지 않고 호출한 쪽으로 올린다.
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
    # state_delta 는 사용자 메시지 이벤트에 실려 먼저 세션에 저장되고,
    # 그 뒤에 에이전트가 돌기 때문에 첫 모델 요청부터 값이 보인다.
    # RunConfig 는 이 run_async 호출 한 번, 즉 한 턴에만 적용된다.
    # 호출 횟수를 세는 카운터가 턴마다 새로 만들어지는 InvocationContext
    # 안에 있어서 다음 턴에는 0 부터 다시 센다.
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=session.id,
        new_message=message,
        state_delta=state,
        run_config=RunConfig(max_llm_calls=max_llm_calls),
    ):
        print(describe(event))
        events.append(event)
    return events


if __name__ == "__main__":
    asyncio.run(
        run(root_agent, " ".join(sys.argv[1:]) or "안녕 하세요 글자 수 세 줘")
    )
