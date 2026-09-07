"""loop_01_pause_resume: yield 가 러너로 제어를 넘기고 다시 받는 지점.

BaseAgent 의 run_async 는 @final 이라 덮어쓸 수 없다. run_async 가
콜백 처리와 InvocationContext 준비를 맡고 _run_async_impl 을 부르므로
하위 클래스는 _run_async_impl 만 채운다. 기본 구현은 호출될 때
NotImplementedError 를 내므로, 빠뜨려도 클래스 정의 시점이 아니라
첫 실행 때 드러난다.
"""

from collections.abc import AsyncGenerator
from typing import override

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from google.genai import types


def _text(text: str) -> types.Content:
    # role 은 대화에서 누가 말했는지다. 에이전트가 낸 말이므로 LLM 이
    # 답할 때와 같은 "model" 을 준다.
    return types.Content(role="model", parts=[types.Part.from_text(text=text)])


class Announcer(BaseAgent):
    """알림 두 개를 이벤트로 내보내는 에이전트."""

    # @override 는 실행에는 아무 영향이 없고 타입 검사기용 표시다.
    # 부모에 같은 이름의 메서드가 없으면 mypy 가 오류를 내므로
    # 메서드 이름을 잘못 적는 실수를 잡아 준다.
    # AsyncGenerator[Event] 는 Python 3.13 부터 허용되는 표기로,
    # 생략한 두 번째 인자(send 타입)는 None 으로 본다.
    @override
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event]:
        print("agent: before yield 1")
        yield Event(
            author=self.name,
            invocation_id=ctx.invocation_id,
            content=_text("첫 번째 알림"),
        )
        # 러너가 위 이벤트를 세션에 저장하고 호출자에게 넘긴 뒤,
        # 호출자가 다음 이벤트를 요청해야 이 줄이 실행된다.
        print("agent: after yield 1")
        print("agent: before yield 2")
        yield Event(
            author=self.name,
            invocation_id=ctx.invocation_id,
            content=_text("두 번째 알림"),
            actions=EventActions(state_delta={"announced": 2}),
        )
        print("agent: after yield 2")


root_agent = Announcer(name="loop_pause")
