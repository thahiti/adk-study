"""runner_02_services: 세션 서비스를 SQLite 로 바꾸고 다른 서비스도 넣는다.

Runner 는 필수인 session_service 외에 artifact_service,
memory_service, credential_service 를 선택으로 받는다. 이 단계는
앞의 셋을 명시하고, 세션 서비스를 SqliteSessionService 로 바꿔
스크립트를 다시 실행해도 같은 session_id 로 대화가 이어지게 한다.

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
    Runner 가 사용자 메시지를 포함한 모든 이벤트를 세션에 저장하고,
    다음 호출에서 그 세션의 이벤트 전체를 모델에 보내기 때문이다.
    """
    # "sqlite:///" 뒤의 경로는 현재 디렉터리 기준 상대경로다.
    # 파일과 테이블은 첫 호출 때 없으면 만들어진다.
    session_service = SqliteSessionService(f"sqlite:///{db_path}")
    # 아티팩트 서비스는 파일 같은 바이너리 데이터를 세션별로
    # 버전을 붙여 보관하고, 메모리 서비스는 지난 세션의 내용을
    # 다른 세션에서 검색하기 위한 저장소다. 둘 다 도구나 콜백이
    # tool_context.save_artifact, search_memory 처럼 직접 불러야
    # 쓰이므로 그런 도구가 없는 이 단계에서는 한 번도 호출되지 않는다.
    # 다만 None 인 채로 그 메서드를 부르면 ValueError 가 난다.
    runner = Runner(
        app_name=APP_NAME,
        agent=agent,
        session_service=session_service,
        artifact_service=InMemoryArtifactService(),
        memory_service=InMemoryMemoryService(),
    )
    # run_async 는 세션을 get_session 으로 찾을 뿐 만들지 않는다.
    # 없으면 SessionNotFoundError 가 나므로 먼저 만들어 둔다.
    # 반대로 이미 있는 id 로 create_session 을 부르면
    # AlreadyExistsError 가 나므로 찾은 뒤 없을 때만 만든다.
    # session_id 를 직접 정하는 이유는 다음 프로세스가 같은 id 로
    # 세션을 다시 찾기 위해서다. 비우면 무작위 uuid 가 된다.
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
