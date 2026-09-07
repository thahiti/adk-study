"""모델 호출 없이 에이전트를 돌리기 위한 테스트 도우미.

FakeLlm 은 미리 정한 응답을 순서대로 돌려주는 BaseLlm 이다.
run_turn 은 InMemoryRunner 로 한 턴을 돌려 이벤트 목록을 준다.
"""

from collections.abc import AsyncGenerator
from typing import Any

from google.adk.agents import BaseAgent
from google.adk.events import Event
from google.adk.models import BaseLlm, LlmRequest, LlmResponse
from google.adk.runners import InMemoryRunner
from google.genai import types
from pydantic import Field


class FakeLlm(BaseLlm):
    """replies 를 순서대로 돌려주고 받은 요청을 requests 에 쌓는다."""

    model: str = "fake"
    replies: list[types.Content]
    requests: list[LlmRequest] = Field(default_factory=list)

    async def generate_content_async(
        self, llm_request: LlmRequest, stream: bool = False
    ) -> AsyncGenerator[LlmResponse]:
        self.requests.append(llm_request)
        yield LlmResponse(content=self.replies.pop(0))


def text_reply(text: str) -> types.Content:
    """모델이 텍스트로 답한 것처럼 보이는 Content 를 만든다."""
    return types.Content(role="model", parts=[types.Part.from_text(text=text)])


def call_reply(name: str, args: dict[str, Any]) -> types.Content:
    """모델이 도구 호출을 요청한 것처럼 보이는 Content 를 만든다."""
    return types.Content(
        role="model",
        parts=[types.Part.from_function_call(name=name, args=args)],
    )


async def run_turn(
    agent: BaseAgent,
    text: str,
    *,
    app_name: str = "test",
    user_id: str = "user",
) -> list[Event]:
    """새 세션을 만들고 사용자 메시지 한 개를 보내 이벤트를 모은다."""
    runner = InMemoryRunner(agent=agent, app_name=app_name)
    session = await runner.session_service.create_session(
        app_name=app_name, user_id=user_id
    )
    message = types.Content(
        role="user", parts=[types.Part.from_text(text=text)]
    )
    return [
        event
        async for event in runner.run_async(
            user_id=user_id, session_id=session.id, new_message=message
        )
    ]
