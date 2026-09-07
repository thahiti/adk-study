"""loop_03_delegation: 커스텀 에이전트가 자식을 돌리고 이벤트를 올린다."""

from collections.abc import AsyncGenerator
from typing import override

from google.adk.agents import BaseAgent, LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai import types

from adk_study.models import make_model


def _text(text: str) -> types.Content:
    return types.Content(role="model", parts=[types.Part.from_text(text=text)])


child = LlmAgent(
    name="loop_child",
    model=make_model(),
    description="부모가 시킨 일을 한 문장으로 답한다",
    instruction="사용자 메시지에 한국어 한 문장으로 답한다.",
)


class Orchestrator(BaseAgent):
    """자식 하나를 돌리고 앞뒤에 자기 이벤트를 붙이는 에이전트."""

    @override
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event]:
        yield Event(
            author=self.name,
            invocation_id=ctx.invocation_id,
            content=_text("시작"),
        )
        # 자식의 run_async 에 내 컨텍스트를 넘기면 자식은 그것을 복사해
        # agent 만 자기로 바꿔 쓴다. 자식이 yield 하는 이벤트를 그대로
        # 다시 yield 해야 러너까지 올라간다.
        async for event in self.sub_agents[0].run_async(ctx):
            yield event
        print("agent: after child")
        yield Event(
            author=self.name,
            invocation_id=ctx.invocation_id,
            content=_text("끝"),
        )


root_agent = Orchestrator(name="loop_orchestrator", sub_agents=[child])
