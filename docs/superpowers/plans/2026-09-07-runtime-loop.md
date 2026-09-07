# runtime-loop 토픽 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** feature/runtime-loop 브랜치에서 Runner 의 for 루프와 에이전트의 yield 사이를 오가는 실행 흐름을 다섯 단계로 보여주고, 리뷰 뒤 main 에 머지하고 푸시한다.

**Architecture:** 각 단계는 adk web 에서 선택할 수 있는 agent.py 와 스크립트 main.py 를 가진다.
main.py 의 `run(agent, text)` 은 러너 쪽에서 이벤트를 받을 때마다 한 줄을 찍고, 에이전트는 yield 전후에 한 줄을 찍어 두 출력이 번갈아 나오는 것을 보인다.
loop_01 은 일시정지와 재개, loop_02 는 yield 뒤 state 반영 확인, loop_03 은 커스텀 오케스트레이터의 위임, loop_04 는 전환 뒤 다음 턴의 에이전트 선택, loop_05 는 플러그인으로 루프를 드러내기다.

**Tech Stack:** google-adk 1.36.2 BaseAgent, InvocationContext, EventActions, BasePlugin, App, pytest capsys

**Spec:** /Users/randy/study/google-adk/docs/superpowers/specs/2026-09-07-adk-study-design.md

## Global Constraints

- 단계 폴더는 `agents/` 바로 아래에 `<토픽>_<두자리 번호>_<이름>` 형식으로 평평하게 둔다. 이 토픽의 접두어는 `loop` 다.
- 단계 추가는 복사 커밋 뒤 수정 커밋으로 나눈다. 복사 커밋 제목은 `copy: <이전> -> <새>` 형식이다.
- 수정 커밋의 Python 코드 변경량은 30줄을 목표로 한다. 복사, README, 테스트는 세지 않는다. 클래스 하나가 학습 단위면 넘어도 되고 본문에 이유를 적는다.
- 커밋 제목은 영어 50자 이내, 본문은 한글이다. Claude나 Anthropic 관련 trailer를 넣지 않는다.
- 주석, 독스트링, README는 한글이고 식별자는 영어다. Python 코드는 79자, 주석과 독스트링은 72자 이내다.
- 모든 커밋에서 `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src agents`가 통과한다. 검사 명령은 파이프 없이 실행해 종료 코드가 가려지지 않게 한다.
- 구현이 끝나면 CLAUDE.md 의 단계 리뷰 규칙대로 단계마다 리뷰 서브에이전트를 보낸 뒤 머지하고 `git push origin main` 한다.

## 1.36.2에서 확인한 사실

- 커스텀 BaseAgent 의 `_run_async_impl` 에서 yield 앞뒤에 print 를 두면, 러너 쪽 for 루프의 print 와 번갈아 찍힌다. 순서는 "agent before 1, runner got 1, agent after 1, agent before 2, runner got 2, agent after 2" 다. yield 한 뒤 다음 줄은 러너가 다음 이벤트를 요청해야 실행된다.
- `EventActions(state_delta=...)` 를 실은 이벤트를 yield 한 뒤 `ctx.session.state` 를 읽으면 그 값이 이미 반영되어 있다. Runner 가 yield 된 이벤트를 `session_service.append_event` 로 저장한 뒤에야 제너레이터를 재개하기 때문이다. yield 전에는 아직 없다.
- 커스텀 에이전트가 `self.sub_agents[0].run_async(ctx)` 로 자식을 돌리고 그 이벤트를 다시 yield 하면, 자식 이벤트는 author 가 자식 name 이고 invocation_id 는 부모와 같다. `BaseAgent.run_async(parent_context)` 는 부모 컨텍스트를 복사해 agent 만 바꾼 컨텍스트를 만든다. `sub_agents` 에 넣으면 `child.parent_agent` 가 자동으로 설정된다.
- LlmAgent 부모가 `transfer_to_agent` 로 자식에게 넘긴 뒤 다음 턴을 보내면 Runner 의 `_find_agent_to_run` 이 세션의 마지막 에이전트 이벤트 author 를 보고 자식을 바로 실행한다. 두 번째 턴에서 부모 모델은 호출되지 않는다.
- `BasePlugin` 의 콜백은 키워드 전용 인자다. `before_run_callback(*, invocation_context)`, `on_event_callback(*, invocation_context, event)`, `after_run_callback(*, invocation_context)`, `before_agent_callback(*, agent, callback_context)`, `after_agent_callback(*, agent, callback_context)`. None 을 돌려주면 흐름을 바꾸지 않는다. 한 턴의 호출 순서는 before_run, before_agent, on_event(이벤트마다), after_agent, after_run 이다.
- 플러그인은 `InMemoryRunner(agent=, app_name=, plugins=[...])` 또는 `Runner(app=App(name=, root_agent=, plugins=[...]), session_service=)` 로 넣는다. agent.py 에 `app` 을 두면 adk web 도 플러그인을 쓴다.

---

### Task 1: 브랜치 생성과 loop_01_pause_resume 복사 커밋

**Files:**
- Create: `agents/loop_01_pause_resume/` (event_04_custom_event 복사)
- Create: `tests/test_loop_01_pause_resume.py` (test_event_04_custom_event.py 복사)

- [ ] **Step 1: 브랜치 생성과 복사**

```bash
git checkout -b feature/runtime-loop
cp -r agents/event_04_custom_event agents/loop_01_pause_resume
rm -rf agents/loop_01_pause_resume/__pycache__ agents/loop_01_pause_resume/.adk
cp tests/test_event_04_custom_event.py tests/test_loop_01_pause_resume.py
```

- [ ] **Step 2: 식별자만 교체**

agent.py 독스트링 접두어를 `"""loop_01_pause_resume:` 로, `root_agent = Announcer(name="event_custom")` 을 `name="loop_pause"` 로 바꾼다.
README 제목을 `# loop_01_pause_resume` 로 바꾼다.
테스트의 독스트링 접두어, import 경로, `"event_custom"` 을 `"loop_pause"` 로 바꾼다.

- [ ] **Step 3: 확인과 커밋**

Run: `uv run pytest tests/test_loop_01_pause_resume.py -q; uv run ruff check .; uv run ruff format --check .`

```bash
git add agents/loop_01_pause_resume tests/test_loop_01_pause_resume.py
git commit -m "copy: event_04_custom_event -> loop_01_pause_resume" -m "yield 전후의 실행 흐름을 보이려면 Event 를 직접 만드는 커스텀 에이전트가
필요하므로 event_04 를 복사한다. main.py 는 다음 커밋에서 더한다."
```

---

### Task 2: loop_01_pause_resume 수정 커밋

**Files:**
- Modify: `agents/loop_01_pause_resume/agent.py`
- Create: `agents/loop_01_pause_resume/main.py`
- Modify: `agents/loop_01_pause_resume/README.md`
- Modify: `tests/test_loop_01_pause_resume.py`

**Interfaces:**
- Produces: `Announcer` 가 yield 전에 `agent: before yield N`, 뒤에 `agent: after yield N` 을 출력한다. `main.run(agent, text) -> list[Event]` 는 이벤트를 받을 때마다 `runner: got <텍스트>` 를 출력한다.

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/test_loop_01_pause_resume.py` 전체:

```python
"""loop_01_pause_resume: yield 가 러너로 제어를 넘기고 다시 받는 지점."""

from agents.loop_01_pause_resume.agent import root_agent
from agents.loop_01_pause_resume.main import run


async def test_agent_and_runner_lines_interleave(capsys):
    await run(root_agent, "시작")

    lines = capsys.readouterr().out.strip().splitlines()
    assert lines == [
        "agent: before yield 1",
        "runner: got 첫 번째 알림",
        "agent: after yield 1",
        "agent: before yield 2",
        "runner: got 두 번째 알림",
        "agent: after yield 2",
    ]


async def test_run_collects_both_events():
    events = await run(root_agent, "시작")

    assert [e.content.parts[0].text for e in events] == [
        "첫 번째 알림",
        "두 번째 알림",
    ]
    assert events[1].actions.state_delta == {"announced": 2}
```

- [ ] **Step 2: 실패 확인**

Run: `uv run pytest tests/test_loop_01_pause_resume.py -q`
Expected: FAIL, `ModuleNotFoundError: No module named 'agents.loop_01_pause_resume.main'`

- [ ] **Step 3: agent.py 수정과 main.py 작성**

`agents/loop_01_pause_resume/agent.py` 의 `_run_async_impl` 을 다음으로 바꾼다. 모듈 독스트링 첫 줄은 `"""loop_01_pause_resume: yield 가 러너로 제어를 넘기고 다시 받는 지점."""` 로 바꾼다.

```python
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
```

`agents/loop_01_pause_resume/main.py`:

```python
"""loop_01_pause_resume: yield 가 러너로 제어를 넘기고 다시 받는 지점.

에이전트는 yield 앞뒤에 한 줄씩 찍고, 러너 쪽 for 루프는 이벤트를
받을 때마다 한 줄 찍는다. 두 출력이 번갈아 나오는 것이 이 단계의
전부다. 에이전트 코드는 이벤트를 한꺼번에 만들어 돌려주는 것이
아니라 하나 내보낼 때마다 멈췄다가 러너가 다음 것을 요청할 때
이어서 돈다.

실행: uv run python -m agents.loop_01_pause_resume.main
"""

import asyncio

from google.adk.agents import BaseAgent
from google.adk.events import Event
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from .agent import root_agent

APP_NAME = "loop_01_pause_resume"
USER_ID = "user"


def text_of(event: Event) -> str:
    """이벤트의 첫 텍스트 파트를 돌려준다. 없으면 빈 문자열이다."""
    parts = event.content.parts if event.content else None
    return parts[0].text or "" if parts else ""


async def run(agent: BaseAgent, text: str) -> list[Event]:
    """메시지 한 개를 보내고 이벤트를 받을 때마다 한 줄 찍는다."""
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
    events: list[Event] = []
    async for event in runner.run_async(
        user_id=USER_ID, session_id=session.id, new_message=message
    ):
        # 이 줄이 찍히는 시점에 에이전트는 yield 에서 멈춰 있다.
        print(f"runner: got {text_of(event)}")
        events.append(event)
    return events


if __name__ == "__main__":
    asyncio.run(run(root_agent, "시작"))
```

- [ ] **Step 4: 통과 확인**

Run: `uv run pytest -q; uv run ruff check .; uv run ruff format --check .; uv run mypy src agents`

- [ ] **Step 5: README 작성**

`agents/loop_01_pause_resume/README.md`:

```markdown
# loop_01_pause_resume

## 이 단계가 보여주는 것

- 에이전트의 `_run_async_impl` 은 async generator 다.
  yield 는 이벤트를 러너에 넘기는 동시에 에이전트를 그 자리에서 멈추는 지점이다.
- 러너는 이벤트를 받으면 세션에 저장하고 호출자(for 루프)에게 넘긴다.
  호출자가 다음 이벤트를 요청해야 에이전트가 yield 다음 줄부터 이어서 돈다.
- 그래서 스크립트 출력은 "agent: before yield 1, runner: got ..., agent: after yield 1" 순서로 번갈아 나온다.
  에이전트가 이벤트를 모두 만든 뒤 러너가 받는 것이 아니다.
- 이 구조 덕분에 러너는 이벤트 하나를 처리(저장, 플러그인, 상태 반영)한 뒤에 에이전트를 재개할 수 있다.
  다음 단계에서 그 결과를 에이전트가 읽는 것을 본다.

## adk web 에서 확인할 것

- 스크립트 `uv run python -m agents.loop_01_pause_resume.main` 을 실행해 여섯 줄의 순서를 본다.
- adk web 에서 메시지를 보내면 알림 두 개가 차례로 나타난다. 터미널에는 agent 쪽 print 만 찍힌다.

## 이전 단계와 다른 점

event_04_custom_event 에 yield 전후 print 와 러너 쪽 print 를 찍는 main.py 가 더해졌다.
```

- [ ] **Step 6: 커밋**

```bash
git add agents/loop_01_pause_resume tests/test_loop_01_pause_resume.py
git commit -m "feat(loop): show pause and resume around yield" -m "러너 루프와 에이전트 제너레이터가 번갈아 도는 것을 출력 순서로 고정한다.
main.py 는 새 파일이라 30줄을 넘는다."
```

---

### Task 3: loop_02_state_commit 복사 커밋

```bash
cp -r agents/loop_01_pause_resume agents/loop_02_state_commit
rm -rf agents/loop_02_state_commit/__pycache__ agents/loop_02_state_commit/.adk
cp tests/test_loop_01_pause_resume.py tests/test_loop_02_state_commit.py
```

agent.py 와 main.py 의 독스트링 접두어, `name="loop_state"`, main.py 의 모듈 경로와 `APP_NAME = "loop_02_state_commit"`, README 제목, 테스트의 접두어와 import 경로를 바꾼다.

Run: `uv run pytest tests/test_loop_02_state_commit.py -q; uv run ruff check .; uv run ruff format --check .`

```bash
git add agents/loop_02_state_commit tests/test_loop_02_state_commit.py
git commit -m "copy: loop_01_pause_resume -> loop_02_state_commit" -m "다음 커밋의 diff 에 yield 뒤 state 읽기만 남기기 위해 이전 단계를 그대로
복사한다."
```

---

### Task 4: loop_02_state_commit 수정 커밋

**Files:**
- Modify: `agents/loop_02_state_commit/agent.py`
- Modify: `agents/loop_02_state_commit/README.md`
- Modify: `tests/test_loop_02_state_commit.py`

**Interfaces:**
- Produces: Announcer 가 둘째 이벤트(state_delta) 를 yield 하기 전에 `agent: announced before yield = None`, 뒤에 `agent: announced after yield = 2` 를 찍고, 셋째 이벤트로 `state 반영 확인: 2` 텍스트를 낸다.

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/test_loop_02_state_commit.py` 전체:

```python
"""loop_02_state_commit: yield 뒤에 state_delta 가 세션에 반영되어 있다."""

from agents.loop_02_state_commit.agent import root_agent
from agents.loop_02_state_commit.main import run


async def test_state_is_visible_only_after_yield(capsys):
    await run(root_agent, "시작")

    lines = capsys.readouterr().out.strip().splitlines()
    assert "agent: announced before yield = None" in lines
    assert "agent: announced after yield = 2" in lines
    assert lines.index("agent: announced before yield = None") < lines.index(
        "runner: got 두 번째 알림"
    )
    assert lines.index("runner: got 두 번째 알림") < lines.index(
        "agent: announced after yield = 2"
    )


async def test_third_event_reports_committed_value():
    events = await run(root_agent, "시작")

    assert events[-1].content.parts[0].text == "state 반영 확인: 2"
    assert events[-1].actions.state_delta == {}
```

- [ ] **Step 2: 실패 확인**

Run: `uv run pytest tests/test_loop_02_state_commit.py -q`
Expected: FAIL

- [ ] **Step 3: agent.py 수정**

`_run_async_impl` 의 둘째 yield 앞뒤를 다음으로 바꾸고, 모듈 독스트링 첫 줄을 `"""loop_02_state_commit: yield 뒤에 state_delta 가 세션에 반영되어 있다."""` 로 바꾼다.

```python
        print("agent: before yield 2")
        # yield 전에는 아직 세션에 없다. 러너가 이 이벤트를 저장해야
        # 반영되기 때문이다.
        print(f"agent: announced before yield = {ctx.session.state.get('announced')}")
        yield Event(
            author=self.name,
            invocation_id=ctx.invocation_id,
            content=_text("두 번째 알림"),
            actions=EventActions(state_delta={"announced": 2}),
        )
        print("agent: after yield 2")
        # 러너가 append_event 로 저장하면서 delta 를 세션 state 에
        # 합친 뒤 재개했으므로 여기서는 값이 보인다.
        announced = ctx.session.state.get("announced")
        print(f"agent: announced after yield = {announced}")
        yield Event(
            author=self.name,
            invocation_id=ctx.invocation_id,
            content=_text(f"state 반영 확인: {announced}"),
        )
```

79자를 넘는 print 는 f-string 을 변수로 나눈다.

- [ ] **Step 4: 통과 확인**

Run: `uv run pytest -q; uv run ruff check .; uv run ruff format --check .; uv run mypy src agents`

- [ ] **Step 5: README 작성**

`agents/loop_02_state_commit/README.md`:

```markdown
# loop_02_state_commit

## 이 단계가 보여주는 것

- state_delta 를 실은 이벤트를 yield 하기 전에는 `ctx.session.state` 에 그 키가 없다.
  yield 한 뒤에는 있다.
- 러너는 이벤트를 받으면 `session_service.append_event` 를 부르고, 세션 서비스가 delta 를 세션 state 에 합친다.
  그 뒤에야 에이전트를 재개하므로 에이전트는 yield 다음 줄에서 반영된 값을 읽을 수 있다.
- 이것이 ADK 런타임의 핵심 약속이다.
  에이전트, 도구, 콜백이 이벤트를 내보낸 뒤 이어서 도는 코드는 그 이벤트가 처리된 뒤의 상태를 본다.
- 셋째 이벤트는 반영된 값을 텍스트로 알린다. 세션의 이벤트 셋 중 둘째만 delta 를 가진다.

## adk web 에서 확인할 것

- 스크립트를 실행해 `announced before yield = None` 과 `after yield = 2` 사이에 `runner: got 두 번째 알림` 이 있는지 본다.
- adk web 에서 메시지를 보내면 셋째 알림에 `state 반영 확인: 2` 가 나오고 State 탭에 announced 가 2 다.

## 이전 단계와 다른 점

loop_01_pause_resume 의 둘째 yield 앞뒤에 state 읽기가 더해지고 셋째 이벤트가 생겼다.
```

- [ ] **Step 6: 커밋**

```bash
git add agents/loop_02_state_commit tests/test_loop_02_state_commit.py
git commit -m "feat(loop): read committed state after yield" -m "yield 전후의 state 값을 찍어 러너가 이벤트를 저장한 뒤에 에이전트를
재개한다는 약속을 보인다."
```

---

### Task 5: loop_03_delegation 복사 커밋

```bash
cp -r agents/loop_02_state_commit agents/loop_03_delegation
rm -rf agents/loop_03_delegation/__pycache__ agents/loop_03_delegation/.adk
cp tests/test_loop_02_state_commit.py tests/test_loop_03_delegation.py
```

독스트링 접두어, `name="loop_orchestrator"`, main.py 모듈 경로와 `APP_NAME = "loop_03_delegation"`, README 제목, 테스트 접두어와 import 경로를 바꾼다.

```bash
git add agents/loop_03_delegation tests/test_loop_03_delegation.py
git commit -m "copy: loop_02_state_commit -> loop_03_delegation" -m "다음 커밋의 diff 에 자식 위임만 남기기 위해 이전 단계를 그대로 복사한다."
```

---

### Task 6: loop_03_delegation 수정 커밋

**Files:**
- Modify: `agents/loop_03_delegation/agent.py`
- Modify: `agents/loop_03_delegation/README.md`
- Modify: `tests/test_loop_03_delegation.py`

**Interfaces:**
- Produces: `child` (LlmAgent, name `loop_child`), `Orchestrator(BaseAgent)`, `root_agent = Orchestrator(name="loop_orchestrator", sub_agents=[child])`. Orchestrator 는 "시작" 이벤트, 자식 이벤트들, "끝" 이벤트 순서로 yield 한다.

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/test_loop_03_delegation.py` 전체:

```python
"""loop_03_delegation: 커스텀 에이전트가 자식을 돌리고 이벤트를 올린다."""

from adk_study.testing import FakeLlm, text_reply
from agents.loop_03_delegation.agent import child, root_agent
from agents.loop_03_delegation.main import run


async def test_child_events_are_reyielded_between_parent_events():
    child.model = FakeLlm(replies=[text_reply("자식이 답함")])

    events = await run(root_agent, "시작")

    assert [(e.author, e.content.parts[0].text) for e in events] == [
        ("loop_orchestrator", "시작"),
        ("loop_child", "자식이 답함"),
        ("loop_orchestrator", "끝"),
    ]


async def test_child_shares_invocation_and_knows_parent():
    child.model = FakeLlm(replies=[text_reply("자식이 답함")])

    events = await run(root_agent, "시작")

    assert len({e.invocation_id for e in events}) == 1
    assert child.parent_agent is root_agent


async def test_runner_line_appears_between_child_and_end(capsys):
    child.model = FakeLlm(replies=[text_reply("자식이 답함")])

    await run(root_agent, "시작")

    lines = capsys.readouterr().out.strip().splitlines()
    assert lines.index("runner: got 자식이 답함") < lines.index(
        "agent: after child"
    )
```

- [ ] **Step 2: 실패 확인**

Run: `uv run pytest tests/test_loop_03_delegation.py -q`
Expected: FAIL, `ImportError: cannot import name 'child'`

- [ ] **Step 3: agent.py 교체**

`agents/loop_03_delegation/agent.py` 전체:

```python
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
            author=self.name, invocation_id=ctx.invocation_id, content=_text("시작")
        )
        # 자식의 run_async 에 내 컨텍스트를 넘기면 자식은 그것을 복사해
        # agent 만 자기로 바꿔 쓴다. 자식이 yield 하는 이벤트를 그대로
        # 다시 yield 해야 러너까지 올라간다.
        async for event in self.sub_agents[0].run_async(ctx):
            yield event
        print("agent: after child")
        yield Event(
            author=self.name, invocation_id=ctx.invocation_id, content=_text("끝")
        )


root_agent = Orchestrator(name="loop_orchestrator", sub_agents=[child])
```

- [ ] **Step 4: 통과 확인**

Run: `uv run pytest -q; uv run ruff check .; uv run ruff format --check .; uv run mypy src agents`

- [ ] **Step 5: README 작성**

`agents/loop_03_delegation/README.md`:

```markdown
# loop_03_delegation

## 이 단계가 보여주는 것

- 커스텀 에이전트는 자식을 직접 돌릴 수 있다.
  `self.sub_agents[0].run_async(ctx)` 가 자식의 이벤트 제너레이터를 돌려주고, 그 이벤트를 다시 yield 해야 러너까지 올라간다.
- 자식은 부모의 InvocationContext 를 복사해 agent 만 자기로 바꿔 쓴다.
  그래서 invocation_id 와 세션이 같고, 자식 이벤트의 author 는 자식 name 이다.
- 자식 이벤트도 러너를 한 번씩 거친다.
  자식이 yield 하면 부모가 다시 yield 하고, 러너가 저장한 뒤에야 부모의 다음 줄이 돈다.
  스크립트에서 `runner: got 자식이 답함` 이 `agent: after child` 보다 먼저 찍히는 것이 그 증거다.
- `sub_agents` 에 넣으면 `child.parent_agent` 가 자동으로 설정된다.
  SequentialAgent 와 ParallelAgent 가 안에서 하는 일이 이것이다.

## adk web 에서 확인할 것

- 메시지를 보내면 "시작", 자식 답, "끝" 세 이벤트가 차례로 나온다.
- Events 탭에서 세 이벤트의 author 가 loop_orchestrator, loop_child, loop_orchestrator 이고 invocationId 가 같다.

## 이전 단계와 다른 점

Announcer 가 자식 LlmAgent 를 품은 Orchestrator 로 바뀌었다. state_delta 는 이 단계의 관심사가 아니라 뺐다.
```

- [ ] **Step 6: 커밋**

```bash
git add agents/loop_03_delegation tests/test_loop_03_delegation.py
git commit -m "feat(loop): delegate to a child from a custom agent" -m "자식 이벤트가 부모의 yield 를 거쳐 러너까지 올라가고 그때마다 러너가
개입한다는 점을 출력 순서와 invocation_id 로 보인다. 클래스 교체라
30줄을 넘는다."
```

---

### Task 7: loop_04_transfer_next_turn 복사 커밋

```bash
cp -r agents/loop_03_delegation agents/loop_04_transfer_next_turn
rm -rf agents/loop_04_transfer_next_turn/__pycache__ agents/loop_04_transfer_next_turn/.adk
cp tests/test_loop_03_delegation.py tests/test_loop_04_transfer_next_turn.py
```

독스트링 접두어, main.py 모듈 경로와 `APP_NAME = "loop_04_transfer_next_turn"`, README 제목, 테스트 접두어와 import 경로를 바꾼다. 에이전트 name 은 다음 커밋에서 바뀌므로 그대로 둔다.

```bash
git add agents/loop_04_transfer_next_turn tests/test_loop_04_transfer_next_turn.py
git commit -m "copy: loop_03_delegation -> loop_04_transfer_next_turn" -m "main.py 의 러너 출력 구조를 이어받기 위해 loop_03 을 복사한다. 에이전트는
다음 커밋에서 LlmAgent 부모와 자식으로 바뀐다."
```

---

### Task 8: loop_04_transfer_next_turn 수정 커밋

**Files:**
- Modify: `agents/loop_04_transfer_next_turn/agent.py`
- Modify: `agents/loop_04_transfer_next_turn/main.py`
- Modify: `agents/loop_04_transfer_next_turn/README.md`
- Modify: `tests/test_loop_04_transfer_next_turn.py`

**Interfaces:**
- Produces: `child` (LlmAgent `loop_specialist`), `root_agent` (LlmAgent `loop_router`, sub_agents=[child]). `main.run_turns(agent, texts) -> list[list[Event]]` 가 한 세션에 메시지를 차례로 보내고 턴마다 `turn N: <author 목록>` 을 찍는다.

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/test_loop_04_transfer_next_turn.py` 전체:

```python
"""loop_04_transfer_next_turn: 전환 뒤 다음 턴은 자식이 바로 이어받는다."""

from adk_study.testing import FakeLlm, call_reply, text_reply
from agents.loop_04_transfer_next_turn.agent import child, root_agent
from agents.loop_04_transfer_next_turn.main import run_turns


def arrange() -> tuple[FakeLlm, FakeLlm]:
    root_agent.model = FakeLlm(
        replies=[call_reply("transfer_to_agent", {"agent_name": "loop_specialist"})]
    )
    child.model = FakeLlm(replies=[text_reply("첫 답"), text_reply("둘째 답")])
    return root_agent.model, child.model


async def test_second_turn_goes_straight_to_child():
    arrange()

    turns = await run_turns(root_agent, ["넘겨 줘", "하나 더"])

    assert [e.author for e in turns[0]] == [
        "loop_router",
        "loop_router",
        "loop_specialist",
    ]
    assert [e.author for e in turns[1]] == ["loop_specialist"]


async def test_parent_model_is_not_called_in_second_turn():
    parent_model, child_model = arrange()

    await run_turns(root_agent, ["넘겨 줘", "하나 더"])

    assert len(parent_model.requests) == 1
    assert len(child_model.requests) == 2


async def test_turn_lines_show_authors(capsys):
    arrange()

    await run_turns(root_agent, ["넘겨 줘", "하나 더"])

    lines = capsys.readouterr().out.strip().splitlines()
    assert lines[-1] == "turn 2: loop_specialist"
```

- [ ] **Step 2: 실패 확인**

Run: `uv run pytest tests/test_loop_04_transfer_next_turn.py -q`
Expected: FAIL, `ImportError`

- [ ] **Step 3: agent.py 와 main.py 교체**

`agents/loop_04_transfer_next_turn/agent.py` 전체:

```python
"""loop_04_transfer_next_turn: 전환 뒤 다음 턴은 자식이 바로 이어받는다."""

from google.adk.agents import LlmAgent

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
```

`agents/loop_04_transfer_next_turn/main.py` 의 `run` 을 `run_turns` 로 바꾼다. 모듈 독스트링은 다음으로 바꾼다.

```python
"""loop_04_transfer_next_turn: 전환 뒤 다음 턴은 자식이 바로 이어받는다.

러너는 턴을 시작할 때 세션의 마지막 에이전트 이벤트 author 를 보고
실행할 에이전트를 고른다. 첫 턴에서 부모가 자식에게 넘겼다면 둘째
턴은 부모를 거치지 않고 자식이 바로 받는다.

실행: uv run python -m agents.loop_04_transfer_next_turn.main
"""
```

```python
async def run_turns(agent: BaseAgent, texts: list[str]) -> list[list[Event]]:
    """한 세션에 메시지를 차례로 보내고 턴마다 author 목록을 찍는다."""
    session_service = InMemorySessionService()
    runner = Runner(
        app_name=APP_NAME, agent=agent, session_service=session_service
    )
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
        authors = ", ".join(e.author for e in events)
        print(f"turn {number}: {authors}")
        turns.append(events)
    return turns


if __name__ == "__main__":
    asyncio.run(run_turns(root_agent, ["넘겨 줘", "하나 더 물어볼게"]))
```

`text_of` 는 쓰지 않으므로 지운다.

- [ ] **Step 4: 통과 확인**

Run: `uv run pytest -q; uv run ruff check .; uv run ruff format --check .; uv run mypy src agents`

- [ ] **Step 5: README 작성**

`agents/loop_04_transfer_next_turn/README.md`:

```markdown
# loop_04_transfer_next_turn

## 이 단계가 보여주는 것

- 러너는 턴마다 root_agent 부터 시작하지 않는다.
  `run_async` 는 세션의 이벤트를 뒤에서부터 보고 마지막 에이전트 이벤트의 author 를 찾아 그 에이전트를 실행한다.
- 첫 턴에서 부모가 `transfer_to_agent` 로 자식에게 넘기면 마지막 이벤트의 author 는 자식이다.
  둘째 턴은 부모 모델을 부르지 않고 자식이 바로 받는다.
- 이 선택은 에이전트 코드가 아니라 러너의 `_find_agent_to_run` 이 한다.
  세션 이력이 곧 다음 턴의 시작점이다.
- 자식에게는 부모로 돌아가는 transfer_to_agent 도구가 붙어 있으므로 필요하면 다시 부모에게 넘길 수 있다.
  `disallow_transfer_to_parent=True` 를 주면 그 길을 막는다.

## adk web 에서 확인할 것

- 첫 메시지를 보내면 Events 탭에 loop_router 의 transfer 와 loop_specialist 의 답이 있다.
- 둘째 메시지를 보내면 loop_specialist 의 답만 생기고 loop_router 이벤트는 없다.
- 스크립트는 `turn 1: loop_router, loop_router, loop_specialist` 와 `turn 2: loop_specialist` 를 찍는다.

## 이전 단계와 다른 점

커스텀 Orchestrator 가 LlmAgent 부모와 자식으로 바뀌고, main.py 가 한 세션에 두 턴을 보낸다.
```

- [ ] **Step 6: 커밋**

```bash
git add agents/loop_04_transfer_next_turn tests/test_loop_04_transfer_next_turn.py
git commit -m "feat(loop): show next-turn agent choice after transfer" -m "러너가 세션의 마지막 author 로 다음 턴의 에이전트를 고른다는 점을 두 턴의
author 목록과 모델 호출 횟수로 보인다. 에이전트 교체와 두 턴 실행이
한 단계라 30줄을 넘는다."
```

---

### Task 9: loop_05_plugin 복사 커밋

```bash
cp -r agents/loop_04_transfer_next_turn agents/loop_05_plugin
rm -rf agents/loop_05_plugin/__pycache__ agents/loop_05_plugin/.adk
cp tests/test_loop_04_transfer_next_turn.py tests/test_loop_05_plugin.py
```

독스트링 접두어, main.py 모듈 경로와 `APP_NAME = "loop_05_plugin"`, README 제목, 테스트 접두어와 import 경로를 바꾼다. 에이전트 name 은 그대로 둔다.

```bash
git add agents/loop_05_plugin tests/test_loop_05_plugin.py
git commit -m "copy: loop_04_transfer_next_turn -> loop_05_plugin" -m "다음 커밋의 diff 에 플러그인 추가만 남기기 위해 이전 단계를 그대로
복사한다."
```

---

### Task 10: loop_05_plugin 수정 커밋

**Files:**
- Modify: `agents/loop_05_plugin/agent.py`
- Modify: `agents/loop_05_plugin/main.py`
- Modify: `agents/loop_05_plugin/README.md`
- Modify: `tests/test_loop_05_plugin.py`

**Interfaces:**
- Produces: `LoopTracer(BasePlugin)` 가 before_run, before_agent, on_event, after_agent, after_run 마다 `plugin: <이름> <에이전트 또는 author>` 를 찍고 `self.log` 에 (이름, 값) 을 쌓는다. `app = App(name="loop_05_plugin", root_agent=root_agent, plugins=[LoopTracer()])`. `main.run_turns` 는 `Runner(app=app, session_service=...)` 로 러너를 만든다.

- [ ] **Step 1: 실패하는 테스트 추가**

`tests/test_loop_05_plugin.py` 에 덧붙인다. import 에 `app` 을 추가한다.

```python
async def test_plugin_sees_run_agent_and_event_hooks_in_order():
    arrange()
    tracer = app.plugins[0]
    tracer.log.clear()

    await run_turns(root_agent, ["넘겨 줘"])

    names = [name for name, _ in tracer.log]
    assert names[0] == "before_run"
    assert names[-1] == "after_run"
    assert names.count("on_event") == 3
    assert names.index("before_agent") < names.index("on_event")


async def test_plugin_sees_child_agent_too():
    arrange()
    tracer = app.plugins[0]
    tracer.log.clear()

    await run_turns(root_agent, ["넘겨 줘"])

    agents_seen = [v for n, v in tracer.log if n == "before_agent"]
    assert agents_seen == ["loop_router", "loop_specialist"]
```

`arrange` 는 그대로 쓰되 `run_turns` 가 app 의 root_agent 를 쓰므로 첫 인자는 무시된다. 시그니처는 유지한다.

- [ ] **Step 2: 실패 확인**

Run: `uv run pytest tests/test_loop_05_plugin.py -q`
Expected: FAIL, `ImportError: cannot import name 'app'`

- [ ] **Step 3: 플러그인 추가**

`agents/loop_05_plugin/agent.py` 끝에 덧붙이고 import 에 `from google.adk.agents import BaseAgent`, `from google.adk.agents.callback_context import CallbackContext`, `from google.adk.agents.invocation_context import InvocationContext`, `from google.adk.apps import App`, `from google.adk.events import Event`, `from google.adk.plugins import BasePlugin`, `from google.genai import types` 를 추가한다. 모듈 독스트링 첫 줄은 `"""loop_05_plugin: 플러그인 콜백으로 러너 루프의 단계를 드러낸다."""` 로 바꾼다.

```python
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
```

`agents/loop_05_plugin/main.py` 에서 `from .agent import root_agent` 를 `from .agent import app, root_agent` 로 바꾸고 Runner 생성을 `Runner(app=app, session_service=session_service)` 로 바꾼다. `agent` 인자는 시그니처에 남기되 쓰지 않으므로 독스트링에 "app 의 root_agent 를 쓴다" 고 적는다. 모듈 독스트링을 다음으로 바꾼다.

```python
"""loop_05_plugin: 플러그인 콜백으로 러너 루프의 단계를 드러낸다.

플러그인은 러너에 붙는 콜백 묶음이다. 턴의 시작과 끝, 에이전트의
시작과 끝, 이벤트 하나하나를 러너가 처리하는 시점에 불린다. adk web
에서도 agent.py 의 app 에 붙인 플러그인이 그대로 돈다.

실행: uv run python -m agents.loop_05_plugin.main
"""
```

- [ ] **Step 4: 통과 확인**

Run: `uv run pytest -q; uv run ruff check .; uv run ruff format --check .; uv run mypy src agents`

- [ ] **Step 5: README 작성**

`agents/loop_05_plugin/README.md`:

```markdown
# loop_05_plugin

## 이 단계가 보여주는 것

- 플러그인은 에이전트가 아니라 러너에 붙는 콜백 묶음이다.
  `BasePlugin` 을 상속해 필요한 콜백만 구현하고 `App(plugins=[...])` 이나 `Runner(plugins=[...])` 로 넣는다.
- 한 턴에서 러너가 부르는 순서는 before_run, before_agent, on_event(이벤트마다), after_agent, after_run 이다.
  자식 에이전트가 돌면 before_agent 와 after_agent 가 자식에 대해서도 불린다.
- on_event 는 러너가 이벤트를 세션에 저장하기 전에 불린다.
  None 을 돌려주면 그대로 두고, Event 를 돌려주면 그것으로 바꾼다. 이 단계는 보기만 한다.
- 콜백은 모두 키워드 전용 인자를 받는다. 시그니처가 다르면 조용히 안 불리는 것이 아니라 TypeError 가 난다.
- agent.py 에 `app` 을 두면 adk web 도 같은 플러그인을 쓰므로, 러너 루프의 각 단계를 터미널 로그로 볼 수 있다.

## adk web 에서 확인할 것

- adk web 을 켠 터미널을 보면서 메시지를 보낸다. `plugin: before_run loop_router` 부터 `plugin: after_run` 까지 찍힌다.
- 둘째 메시지에서는 before_agent 가 loop_specialist 만 나온다. 앞 단계에서 본 다음 턴 선택이 플러그인 로그로도 확인된다.
- 스크립트는 같은 로그를 turn 줄과 함께 찍는다.

## 이전 단계와 다른 점

loop_04_transfer_next_turn 에 LoopTracer 플러그인과 App 이 더해지고, main.py 가 Runner(app=app) 으로 러너를 만든다.
```

- [ ] **Step 6: 커밋**

```bash
git add agents/loop_05_plugin tests/test_loop_05_plugin.py
git commit -m "feat(loop): trace runner hooks with a plugin" -m "러너 루프의 단계를 플러그인 콜백 순서로 드러내고 adk web 에서도 같은
로그가 나오게 App 에 붙인다. 플러그인 클래스 하나가 학습 단위라 30줄을
넘는다."
```

---

### Task 11: 리뷰, README 갱신, 머지, 푸시

- [ ] **Step 1: 단계 리뷰**

CLAUDE.md 의 단계 리뷰 규칙대로 다섯 단계에 리뷰 서브에이전트를 병렬로 보낸다. main.py 도 리뷰 대상에 넣는다. 결과를 확인하고 단계마다 `docs(loop): ...` 로 커밋한다.

- [ ] **Step 2: 표에 runtime-loop 줄 추가**

```markdown
| 7 | runtime-loop | loop_01_pause_resume, loop_02_state_commit, loop_03_delegation, loop_04_transfer_next_turn, loop_05_plugin |
```

```bash
git add README.md
git commit -m "docs: add runtime-loop topic to study order" -m "머지 전에 학습 순서 표를 갱신해 드롭다운 알파벳순과 학습 순서를 잇는다."
```

- [ ] **Step 3: 전체 검사, 머지, 푸시**

```bash
git rebase main
git checkout main
git merge --no-ff feature/runtime-loop -m "merge: runtime-loop 토픽" -m "yield 의 일시정지와 재개, yield 뒤 state 반영, 자식 위임, 전환 뒤 다음 턴
선택, 플러그인 훅 다섯 단계로 러너의 for 루프와 에이전트 사이의 실행
흐름을 보인다."
git branch -d feature/runtime-loop
git push origin main
```
