"""loop_02_state_commit: yield 뒤에 state_delta 가 세션에 반영되어 있다.

BaseAgent 하위 클래스가 run_async 대신 _run_async_impl 만 채우는
이유는 loop_01_pause_resume 에 적었다.

state_delta 는 이벤트에 실려 나갈 뿐 그 자체로 세션을 바꾸지
않는다. 러너가 이벤트를 session_service.append_event 로 저장할 때
세션 서비스가 delta 를 세션 state 에 합친다. 러너는 그때
ctx.session 을 그대로 넘기므로, 저장이 끝나면 여기서 읽는
ctx.session.state 가 이미 바뀌어 있다.
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
    """알림 두 개를 내보낸 뒤 반영된 state 를 알리는 에이전트."""

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
        # 아직 없다. delta 는 아래에서 만들 Event 안에만 있고,
        # ctx.session.state 는 세션에 저장된 값만 담은 평범한 dict 라
        # 저장되지 않은 delta 가 비쳐 보이지 않는다. 도구와 콜백이
        # 받는 tool_context.state 는 delta 를 겹쳐 보여 주는 State
        # 래퍼라 규칙이 다르다.
        before = ctx.session.state.get("announced")
        print(f"agent: announced before yield = {before}")
        yield Event(
            author=self.name,
            invocation_id=ctx.invocation_id,
            content=_text("두 번째 알림"),
            actions=EventActions(state_delta={"announced": 2}),
        )
        print("agent: after yield 2")
        # 러너가 append_event 로 저장하면서 delta 를 세션 state 에
        # 합쳤고, 그 뒤에야 이 줄이 실행되므로 값이 보인다. 세션
        # 서비스 종류와 상관없이 같다. 모든 서비스가 합치는 일을 하는
        # BaseSessionService.append_event 를 거치기 때문이다.
        announced = ctx.session.state.get("announced")
        print(f"agent: announced after yield = {announced}")
        # 이 이벤트에는 state_delta 를 싣지 않는다. 값을 또 쓰는 것이
        # 아니라 이미 반영된 값을 읽어 알리기만 하기 때문이다.
        yield Event(
            author=self.name,
            invocation_id=ctx.invocation_id,
            content=_text(f"state 반영 확인: {announced}"),
        )


root_agent = Announcer(name="loop_state")
