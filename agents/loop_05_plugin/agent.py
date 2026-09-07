"""loop_05_plugin: 플러그인 콜백으로 러너 루프의 단계를 드러낸다."""

from google.adk.agents import BaseAgent, LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.invocation_context import InvocationContext
from google.adk.apps import App
from google.adk.events import Event
from google.adk.plugins import BasePlugin
from google.genai import types

from adk_study.models import make_model

child = LlmAgent(
    name="loop_specialist",
    model=make_model(),
    description="넘겨받은 뒤의 대화를 계속 맡는다",
    instruction="사용자 메시지에 한국어 한 문장으로 답한다.",
)

root_agent = LlmAgent(
    name="loop_router",
    model=make_model(),
    description="첫 메시지를 받아 전문가에게 넘긴다",
    instruction="사용자 요청은 loop_specialist 에게 넘긴다.",
    sub_agents=[child],
)


class LoopTracer(BasePlugin):
    """러너가 부르는 콜백마다 한 줄 찍고 log 에 쌓는다."""

    def __init__(self) -> None:
        super().__init__(name="loop_tracer")
        self.log: list[tuple[str, str]] = []

    def _note(self, name: str, value: str) -> None:
        self.log.append((name, value))
        print(f"plugin: {name} {value}")

    async def before_run_callback(
        self, *, invocation_context: InvocationContext
    ) -> types.Content | None:
        self._note("before_run", invocation_context.agent.name)
        return None

    async def before_agent_callback(
        self, *, agent: BaseAgent, callback_context: CallbackContext
    ) -> types.Content | None:
        self._note("before_agent", agent.name)
        return None

    async def on_event_callback(
        self, *, invocation_context: InvocationContext, event: Event
    ) -> Event | None:
        self._note("on_event", event.author)
        return None

    async def after_agent_callback(
        self, *, agent: BaseAgent, callback_context: CallbackContext
    ) -> types.Content | None:
        self._note("after_agent", agent.name)
        return None

    async def after_run_callback(
        self, *, invocation_context: InvocationContext
    ) -> None:
        self._note("after_run", invocation_context.agent.name)


app = App(name="loop_05_plugin", root_agent=root_agent, plugins=[LoopTracer()])
