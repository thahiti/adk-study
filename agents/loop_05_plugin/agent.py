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
    """러너가 부르는 콜백마다 한 줄 찍고 log 에 쌓는다.

    콜백은 모두 키워드 전용 인자를 받는다. PluginManager 가
    callback(**kwargs) 로 부르기 때문에 인자 이름이 하나라도 다르면
    조용히 안 불리는 것이 아니라 예외가 난다.

    콜백이 None 이 아닌 값을 돌려주면 남은 플러그인과 에이전트 자신의
    콜백을 건너뛰고 그 값이 결과가 된다. 이 단계는 보기만 하므로 모두
    None 을 돌려준다.

    구현하지 않은 콜백은 BasePlugin 의 빈 기본 구현이 대신한다. 여기서
    쓰는 다섯 개 말고도 before_model, after_model, before_tool,
    after_tool, on_user_message, on_model_error, on_tool_error 가 있다.
    """

    def __init__(self) -> None:
        # BasePlugin 은 이름으로 플러그인을 구분한다. 한 러너에 같은
        # 이름을 두 번 등록하면 ValueError 가 난다.
        super().__init__(name="loop_tracer")
        self.log: list[tuple[str, str]] = []

    def _note(self, name: str, value: str) -> None:
        # 화면으로 순서를 보고 테스트로는 log 를 검사하려고 둘 다 남긴다.
        self.log.append((name, value))
        print(f"plugin: {name} {value}")

    async def before_run_callback(
        self, *, invocation_context: InvocationContext
    ) -> types.Content | None:
        # 러너가 실행할 에이전트를 고른 뒤에 불리므로 여기의 agent 는
        # 늘 root_agent 가 아니다. 전환 뒤의 턴에서는 자식이 들어온다.
        self._note("before_run", invocation_context.agent.name)
        return None

    async def before_agent_callback(
        self, *, agent: BaseAgent, callback_context: CallbackContext
    ) -> types.Content | None:
        # 에이전트마다 불린다. 부모가 자식에게 넘기면 같은 턴 안에서
        # 자식 몫이 한 번 더 불린다.
        self._note("before_agent", agent.name)
        return None

    async def on_event_callback(
        self, *, invocation_context: InvocationContext, event: Event
    ) -> Event | None:
        # 러너가 이벤트를 세션에 저장하기 직전에 불린다. 여기서 Event 를
        # 돌려주면 저장본과 호출자가 받는 이벤트가 함께 바뀐다.
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
        # 유일하게 반환 타입이 None 인 콜백이다. 실행을 바꿀 수 없고
        # 정리와 기록만 한다.
        self._note("after_run", invocation_context.agent.name)


# adk web 은 agent.py 에서 app 을 먼저 찾고 없을 때만 root_agent 를 쓴다.
# 그래서 여기에 App 을 두면 웹에서도 같은 플러그인이 돈다. 이 인스턴스는
# 모듈 전역이라 log 는 프로세스가 사는 동안 계속 쌓인다.
app = App(name="loop_05_plugin", root_agent=root_agent, plugins=[LoopTracer()])
