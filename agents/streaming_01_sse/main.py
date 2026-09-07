"""streaming_01_sse: SSE 모드에서 partial 이벤트를 조각으로 받는다.

RunConfig(streaming_mode=StreamingMode.SSE) 를 주면 모델이 내는
텍스트 조각이 partial=True 이벤트로 하나씩 온다. 마지막에 전체
텍스트를 담은 partial=False 이벤트가 오고 세션에는 그것만 남는다.

SSE 는 Server-Sent Events 의 약자다. adk web 서버가 이벤트를 브라우저로
흘려보낼 때 쓰는 HTTP 방식에서 이름을 따 왔을 뿐, 스크립트에서는
HTTP 없이 run_async 가 partial 이벤트를 yield 하는 모드를 뜻한다.

실행: uv run python -m agents.streaming_01_sse.main [메시지]
"""

import asyncio
import sys

from google.adk.agents import BaseAgent
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.events import Event
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from .agent import root_agent

# Runner 는 에이전트가 정의된 agents/ 아래 폴더 이름을 app_name 으로
# 기대한다. 다르면 경고 로그를 남기므로 폴더 이름과 같게 둔다.
APP_NAME = "streaming_01_sse"
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
    agent: BaseAgent, text: str, *, streaming: bool = True
) -> list[Event]:
    """세션 하나를 만들고 메시지 한 개를 보내 이벤트를 출력하고 모은다.

    streaming 이 True 면 SSE 모드라 partial 이벤트가 조각으로 오고,
    False 면 NONE 모드라 최종 이벤트만 온다.
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
    # 스트리밍은 에이전트나 Runner 의 속성이 아니라 run_async 호출 한
    # 번에 붙는 RunConfig 로 정한다. 같은 Runner 로 턴마다 다르게 줄 수
    # 있다. LlmFlow 는 이 값이 SSE 일 때만 모델의
    # generate_content_async 에 stream=True 를 넘긴다.
    mode = StreamingMode.SSE if streaming else StreamingMode.NONE
    events: list[Event] = []
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=session.id,
        new_message=message,
        run_config=RunConfig(streaming_mode=mode),
    ):
        # partial 은 Optional[bool] 이라 NONE 모드에서는 None 일 수도
        # 있다. 참인지로만 가르면 None 과 False 를 같이 최종으로 본다.
        if event.partial:
            # 조각 이벤트는 그 조각의 텍스트만 담으므로 줄바꿈 없이
            # 이어 찍어야 한 문장이 된다. 개행이 없으면 stdout 버퍼가
            # 비워지지 않아 최종 이벤트까지 화면에 아무것도 안 보이므로
            # flush 로 조각마다 바로 내보낸다.
            parts = event.content.parts if event.content else None
            print(parts[0].text if parts else "", end="", flush=True)
        else:
            # 조각 줄은 개행 없이 끝나 있어서 요약을 새 줄에 찍는다.
            # NONE 모드나 조각 없이 오는 이벤트 앞에는 빈 줄이 하나 생긴다.
            print()
            print(describe(event))
        events.append(event)
    return events


if __name__ == "__main__":
    asyncio.run(
        run(
            root_agent,
            " ".join(sys.argv[1:]) or "자기소개를 세 문장으로 해 줘",
        )
    )
