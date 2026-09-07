"""streaming_02_compare: NONE 과 SSE 를 같은 메시지로 비교한다.

루프에 나오는 이벤트 수는 모드에 따라 다르지만 세션에 저장되는
이벤트 수는 같다. 스트리밍은 전달 방식의 차이일 뿐 대화 기록을 바꾸지
않는다. 모델 호출도 두 모드 모두 한 번이다. LlmFlow 는
generate_content_async 를 한 번 부르고 stream 인자만 모드에 따라
바꾼다.

실행: uv run python -m agents.streaming_02_compare.main [메시지]
"""

import asyncio
import sys

from google.adk.agents import BaseAgent
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.events import Event
from google.adk.runners import Runner
from google.adk.sessions import BaseSessionService, InMemorySessionService
from google.genai import types

from .agent import root_agent

# Runner 는 에이전트가 정의된 agents/ 아래 폴더 이름을 app_name 으로
# 기대한다. 다르면 경고 로그를 남기므로 폴더 이름과 같게 둔다.
APP_NAME = "streaming_02_compare"
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
    return f"[{event.author}] text {text}"


async def run(
    agent: BaseAgent,
    text: str,
    *,
    streaming: bool = True,
    session_service: BaseSessionService | None = None,
) -> list[Event]:
    """세션 하나를 만들고 메시지 한 개를 보내 이벤트를 출력하고 모은다.

    streaming 이 True 면 SSE 모드라 partial 이벤트가 조각으로 오고,
    False 면 NONE 모드라 최종 이벤트만 온다.

    반환값은 루프에 나온 이벤트라 세션에 무엇이 저장됐는지는 알 수
    없다. 저장된 이벤트까지 보려는 호출자는 session_service 를 넘겨
    같은 서비스를 나중에 조회한다. 안 넘기면 이전 단계처럼 안에서
    만들어 쓴다.
    """
    session_service = session_service or InMemorySessionService()
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


async def compare(agent: BaseAgent, text: str) -> dict[str, int]:
    """같은 메시지를 NONE 과 SSE 로 돌려 이벤트 수를 비교한다.

    루프에 나온 이벤트 수는 다르지만 세션에 저장된 이벤트 수는 같다.
    저장 수는 출력만 하고 반환값에는 루프 이벤트 수만 담는다.
    """
    counts: dict[str, int] = {}
    for name, streaming in (("none", False), ("sse", True)):
        # 모드마다 서비스를 새로 만들어 세션이 하나만 있게 한다.
        # 서비스를 공유하면 두 번째 모드에서 세션이 둘이 되어
        # list_sessions 결과에서 어느 것이 이번 것인지 골라야 한다.
        session_service = InMemorySessionService()
        events = await run(
            agent, text, streaming=streaming, session_service=session_service
        )
        # run 은 세션 id 를 돌려주지 않으므로 list_sessions 로 찾는다.
        # InMemorySessionService.list_sessions 는 events 를 비운 복사본을
        # 주므로 이벤트를 세려면 get_session 을 한 번 더 불러야 한다.
        listed = await session_service.list_sessions(
            app_name=APP_NAME, user_id=USER_ID
        )
        session = await session_service.get_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=listed.sessions[0].id,
        )
        # get_session 은 없는 id 면 None 을 주는 시그니처라 분기가 필요하다.
        stored = len(session.events) if session else 0
        print(f"{name}: events={len(events)} stored={stored}")
        counts[name] = len(events)
    return counts


if __name__ == "__main__":
    asyncio.run(
        run(
            root_agent,
            " ".join(sys.argv[1:]) or "자기소개를 세 문장으로 해 줘",
        )
    )
