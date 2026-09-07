"""loop_01_pause_resume: yield 가 러너로 제어를 넘기고 다시 받는 지점.

BaseAgent 를 상속해 _run_async_impl 만 채우는 이유는
event_04_custom_event 에서 다뤘다. 여기서 볼 것은 그 메서드가
async generator 라는 사실 하나다.

async generator 는 불러도 몸통이 실행되지 않고 생성자 객체만
만들어진다. 몸통은 호출자가 __anext__ 를 부를 때(async for 한
바퀴) 다음 yield 까지만 돈다. yield 는 값을 넘기면서 함수를 그
줄에서 멈추고 지역 변수와 실행 위치를 그대로 남겨 둔다. 그래서
yield 앞뒤에 print 를 두면, 러너가 이벤트 하나를 다 처리하고
다음 것을 요청하기 전까지 뒷줄이 실행되지 않는 것이 눈에 보인다.

이 print 는 학습용이다. 실제 에이전트에 넣을 코드가 아니다.
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
        # 러너가 위 이벤트를 플러그인 콜백에 태우고 세션에 저장한 뒤
        # 호출자에게 넘기고, 호출자가 다음 이벤트를 요청해야 이 줄이
        # 실행된다. 그래서 출력에서 이 줄은 runner 쪽 줄 다음이다.
        print("agent: after yield 1")
        print("agent: before yield 2")
        yield Event(
            author=self.name,
            invocation_id=ctx.invocation_id,
            content=_text("두 번째 알림"),
            actions=EventActions(state_delta={"announced": 2}),
        )
        # 마지막 yield 뒤에도 몸통이 조금 남아 있다. 이 줄은 호출자가
        # 한 번 더 요청할 때 실행되고, 그 요청은 새 이벤트 대신
        # 생성자 종료로 끝나 async for 루프를 빠져나가게 한다.
        print("agent: after yield 2")


root_agent = Announcer(name="loop_pause")
