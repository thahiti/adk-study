"""loop_05_plugin: 플러그인 콜백으로 러너 루프의 단계를 드러낸다.

플러그인은 러너에 붙는 콜백 묶음이다. 턴의 시작과 끝, 에이전트의
시작과 끝, 이벤트 하나하나를 러너가 처리하는 시점에 불린다. adk web
에서도 agent.py 의 app 에 붙인 플러그인이 그대로 돈다.

실행: uv run python -m agents.loop_05_plugin.main
"""

import asyncio

from google.adk.agents import BaseAgent
from google.adk.events import Event
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from .agent import app, root_agent

APP_NAME = "loop_05_plugin"
USER_ID = "user"


async def run_turns(agent: BaseAgent, texts: list[str]) -> list[list[Event]]:
    """한 세션에 메시지를 차례로 보내고 턴마다 author 목록을 찍는다.

    러너는 app 으로 만들므로 플러그인이 함께 붙는다. 실행되는
    에이전트는 app 의 root_agent 이고 agent 인자는 앞 단계와 같은
    시그니처를 유지하기 위한 것이다.

    즉 agent 인자는 여기서 쓰이지 않는다. Runner 에 app 과 agent 를
    같이 넘기면 ValueError 가 나므로 넘기지 않는다. app_name 도 주지
    않으면 app.name 을 그대로 쓴다.
    """
    session_service = InMemorySessionService()
    runner = Runner(app=app, session_service=session_service)
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
        # plugin 줄이 먼저 흐르고 턴이 끝난 뒤 이 줄이 찍힌다.
        authors = ", ".join(e.author for e in events)
        print(f"turn {number}: {authors}")
        turns.append(events)
    return turns


if __name__ == "__main__":
    asyncio.run(run_turns(root_agent, ["넘겨 줘", "하나 더 물어볼게"]))
