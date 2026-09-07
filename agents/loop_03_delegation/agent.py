"""loop_03_delegation: 커스텀 에이전트가 자식을 돌리고 이벤트를 올린다.

자식은 _run_async_impl 이 아니라 run_async 로 부른다. run_async 가
자식 몫의 InvocationContext 를 만들고 자식의 before/after agent
콜백을 돌려 주기 때문이다. 그 콜백들은 부모의 콜백과 별개로 자식
차례에만 돈다.
"""

from collections.abc import AsyncGenerator
from typing import override

from google.adk.agents import BaseAgent, LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai import types

from adk_study.models import make_model


def _text(text: str) -> types.Content:
    return types.Content(role="model", parts=[types.Part.from_text(text=text)])


# description 은 모델이 위임 대상을 고를 때 읽는 설명이다. 여기서는
# 부모가 코드로 직접 자식을 부르므로 모델 판단에 쓰이지 않고, adk web
# 의 에이전트 트리에만 보인다.
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
        # 자식의 run_async 에 내 컨텍스트를 넘기면 자식은 그것을 얕게
        # 복사해 agent 만 자기로 바꿔 쓴다. invocation_id, session,
        # branch 는 부모 것 그대로다. 자식을 sub_agents 로 등록해 두면
        # parent_agent 가 붙어 에이전트 트리가 생기므로, 모듈 전역
        # child 대신 트리를 통해 꺼낸다.
        # 러너는 root_agent 하나만 돌린다. 자식이 yield 한 이벤트를
        # 부모가 다시 yield 해야 러너까지 올라간다.
        async for event in self.sub_agents[0].run_async(ctx):
            yield event
        # 이 줄은 자식의 마지막 이벤트를 러너가 이미 받아 저장한 뒤에야
        # 실행된다. 자식 이벤트가 부모를 거쳐 러너까지 갔다 왔다는 표시다.
        print("agent: after child")
        yield Event(
            author=self.name,
            invocation_id=ctx.invocation_id,
            content=_text("끝"),
        )


# 이 생성자가 도는 순간 model_post_init 이 sub_agents 를 훑어
# child.parent_agent 에 자기를 박는다. 만들어 둔 에이전트의
# sub_agents 리스트에 나중에 append 하면 붙지 않는다.
root_agent = Orchestrator(name="loop_orchestrator", sub_agents=[child])
