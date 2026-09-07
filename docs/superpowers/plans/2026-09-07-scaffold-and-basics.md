# 스캐폴드와 basics 토픽 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** uv 프로젝트 스캐폴드를 main에 만들고, feature/basics 브랜치에서 최소 LlmAgent 두 단계를 adk web에서 실행 가능하게 만든 뒤 main에 머지한다.

**Architecture:** 루트 pyproject.toml 하나가 `src/adk_study`(공용 코드)와 `agents`(단계 폴더) 두 패키지를 설치한다.
모델은 `adk_study.models.make_model()`이 `.env`의 MODEL_NAME으로 LiteLlm을 만들어 준다.
테스트는 `adk_study.testing.FakeLlm`으로 모델을 바꿔 끼우고 InMemoryRunner로 한 턴을 돌려 이벤트를 검사한다.

**Tech Stack:** Python 3.13, uv, google-adk[extensions] 1.36.2 (litellm 1.83.14 포함), ruff, mypy, pytest, pytest-asyncio

**Spec:** /Users/randy/study/google-adk/docs/superpowers/specs/2026-09-07-adk-study-design.md

## Global Constraints

- google-adk는 `google-adk[extensions]>=1.36.2,<1.37`로 고정한다.
- Python은 3.13이다. 1.36.2는 3.14를 지원하지 않는다.
- 단계 폴더는 `agents/` 바로 아래에 `<토픽>_<두자리 번호>_<이름>` 형식으로 평평하게 둔다.
- 모델은 `LiteLlm(model="openai/<모델명>")`만 쓴다. `google.adk.labs.openai`는 1.36.2에 없다.
- 단계 추가는 복사 커밋 뒤 수정 커밋으로 나눈다. 복사 커밋 제목은 `copy: <이전> -> <새>` 형식이다.
- 수정 커밋의 Python 코드 변경량은 30줄을 목표로 한다. 복사, 스캐폴드, uv.lock, README, 테스트는 세지 않는다.
- 커밋 제목은 영어 50자 이내, 본문은 한글이다. Claude나 Anthropic 관련 trailer를 넣지 않는다.
- 주석, 독스트링, README는 한글이고 식별자는 영어다. Python 코드는 79자, 주석과 독스트링은 72자 이내다.
- 환경변수는 `.env`에서만 읽는다. `.env`는 커밋하지 않는다.
- 사실 확인은 `.venv/lib/python3.13/site-packages/google/adk/`의 설치된 코드 기준이다.

---

### Task 1: uv 프로젝트 스캐폴드 (main)

**Files:**
- Create: `pyproject.toml`
- Create: `.python-version`
- Create: `src/adk_study/__init__.py`
- Create: `agents/__init__.py`
- Create: `uv.lock` (uv sync가 생성)

**Interfaces:**
- Produces: 설치된 패키지 `adk_study`, `agents`. 이후 모든 태스크가 `uv run`으로 실행한다.

- [ ] **Step 1: pyproject.toml 작성**

```toml
[project]
name = "adk-study"
version = "0.1.0"
description = "Google ADK 1.36.x 핵심 개념을 단계별로 익히는 학습 프로젝트"
readme = "README.md"
requires-python = ">=3.13,<3.14"
dependencies = [
    "google-adk[extensions]>=1.36.2,<1.37",
]

[dependency-groups]
dev = [
    "ruff>=0.16",
    "mypy>=1.15",
    "pytest>=8.3",
    "pytest-asyncio>=1.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/adk_study", "agents"]

[tool.ruff]
line-length = 79
target-version = "py313"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]

[tool.mypy]
python_version = "3.13"
ignore_missing_imports = true
check_untyped_defs = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 2: 패키지 뼈대와 Python 버전 고정**

```bash
echo "3.13" > .python-version
mkdir -p src/adk_study agents
printf '"""ADK 학습 프로젝트 공용 코드."""\n' > src/adk_study/__init__.py
printf '"""adk web agents 로 실행하는 단계 폴더 모음."""\n' > agents/__init__.py
```

`README.md`는 pyproject가 참조하므로 임시로 제목만 둔다. 내용은 Task 4에서 채운다.

```bash
printf '# ADK 학습 프로젝트\n' > README.md
```

- [ ] **Step 3: uv sync 실행과 설치 확인**

Run: `uv sync`
Expected: `.venv` 생성, `uv.lock` 생성, 오류 없음

Run: `uv run python -c "import google.adk, adk_study, agents; print(google.adk.__version__)"`
Expected: `1.36.2`

Run: `uv run ruff check . && uv run ruff format --check .`
Expected: `All checks passed!`

- [ ] **Step 4: 커밋**

```bash
git add pyproject.toml .python-version uv.lock README.md src/adk_study/__init__.py agents/__init__.py
git commit -m "chore: scaffold uv project with google-adk 1.36.2" -m "학습 대상 버전을 1.36.x로 고정하고 3.13 이하만 지원하므로 python도
3.13으로 못 박는다. agents 폴더를 src와 함께 설치되는 패키지로 두어
러너 스크립트를 python -m 으로 실행할 수 있게 한다."
```

---

### Task 2: 모델 생성 공용 코드

**Files:**
- Create: `src/adk_study/models.py`
- Create: `.env.example`
- Test: `tests/test_models.py`

**Interfaces:**
- Produces: `make_model() -> LiteLlm`. 모든 단계의 agent.py가 이 함수로 모델을 만든다.
- Produces: `DEFAULT_MODEL = "gpt-4o-mini"`

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/test_models.py`:

```python
"""make_model이 .env의 MODEL_NAME을 반영하는지 확인한다."""

from adk_study.models import DEFAULT_MODEL, make_model


def test_default_model_when_env_missing(monkeypatch):
    monkeypatch.delenv("MODEL_NAME", raising=False)
    model = make_model()
    assert model.model == f"openai/{DEFAULT_MODEL}"


def test_model_name_from_env(monkeypatch):
    monkeypatch.setenv("MODEL_NAME", "gpt-4o")
    model = make_model()
    assert model.model == "openai/gpt-4o"
```

- [ ] **Step 2: 실패 확인**

Run: `uv run pytest tests/test_models.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'adk_study.models'`

- [ ] **Step 3: 구현**

`src/adk_study/models.py`:

```python
"""모델 생성 공용 코드.

모든 단계는 이 모듈의 make_model 로만 모델을 만든다.
1.36.2에서 OpenAI 모델은 LiteLlm 을 통해서만 쓸 수 있다.
"""

import os

from dotenv import load_dotenv
from google.adk.models.lite_llm import LiteLlm

DEFAULT_MODEL = "gpt-4o-mini"


def make_model() -> LiteLlm:
    """.env 의 MODEL_NAME 으로 OpenAI 모델을 만든다.

    adk web 은 .env 를 먼저 읽지만 python -m 으로 실행하는
    스크립트는 그렇지 않으므로 여기서 load_dotenv 를 부른다.
    """
    load_dotenv()
    name = os.environ.get("MODEL_NAME", DEFAULT_MODEL)
    return LiteLlm(model=f"openai/{name}")
```

`.env.example`:

```
OPENAI_API_KEY=sk-...
MODEL_NAME=gpt-4o-mini
```

- [ ] **Step 4: 통과 확인**

Run: `uv run pytest tests/test_models.py -v`
Expected: 2 passed

Run: `uv run ruff check . && uv run ruff format --check . && uv run mypy src agents`
Expected: 오류 없음. ruff format이 고치자고 하면 `uv run ruff format .` 후 다시 확인한다.

- [ ] **Step 5: 커밋**

```bash
git add src/adk_study/models.py .env.example tests/test_models.py
git commit -m "feat(models): add make_model reading MODEL_NAME" -m "단계마다 모델 생성 코드를 반복하면 학습 diff 에 잡음이 섞이므로 공용
함수 하나로 모은다. 모델명은 .env 에서 읽어 실행 환경에 따라 바꿀 수
있게 한다."
```

---

### Task 3: 테스트용 가짜 모델과 한 턴 실행 도우미

**Files:**
- Create: `src/adk_study/testing.py`
- Test: `tests/test_testing.py`

**Interfaces:**
- Produces: `FakeLlm(replies=[...])`, `text_reply(text) -> Content`, `call_reply(name, args) -> Content`, `run_turn(agent, text) -> list[Event]`
- 이후 모든 단계 테스트가 이 넷을 쓴다.

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/test_testing.py`:

```python
"""FakeLlm 과 run_turn 이 실제 Runner 흐름을 재현하는지 확인한다."""

from google.adk.agents import LlmAgent

from adk_study.testing import FakeLlm, call_reply, run_turn, text_reply


def echo(word: str) -> str:
    """받은 단어를 그대로 돌려준다."""
    return word


async def test_text_reply_becomes_final_event():
    fake = FakeLlm(replies=[text_reply("안녕하세요")])
    agent = LlmAgent(name="t", model=fake, instruction="인사")

    events = await run_turn(agent, "안녕")

    assert len(events) == 1
    assert events[0].is_final_response()
    assert events[0].content.parts[0].text == "안녕하세요"
    assert len(fake.requests) == 1


async def test_call_reply_runs_tool_then_final():
    fake = FakeLlm(
        replies=[call_reply("echo", {"word": "x"}), text_reply("끝")]
    )
    agent = LlmAgent(name="t", model=fake, instruction="", tools=[echo])

    events = await run_turn(agent, "x 라고 말해")

    assert events[0].get_function_calls()[0].name == "echo"
    assert events[1].get_function_responses()[0].response == {
        "result": "x"
    }
    assert events[2].is_final_response()
    assert len(fake.requests) == 2
```

- [ ] **Step 2: 실패 확인**

Run: `uv run pytest tests/test_testing.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'adk_study.testing'`

- [ ] **Step 3: 구현**

`src/adk_study/testing.py`:

```python
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
    ) -> AsyncGenerator[LlmResponse, None]:
        self.requests.append(llm_request)
        yield LlmResponse(content=self.replies.pop(0))


def text_reply(text: str) -> types.Content:
    """모델이 텍스트로 답한 것처럼 보이는 Content 를 만든다."""
    return types.Content(
        role="model", parts=[types.Part.from_text(text=text)]
    )


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
```

- [ ] **Step 4: 통과 확인**

Run: `uv run pytest tests/test_testing.py -v`
Expected: 2 passed

Run: `uv run ruff check . && uv run ruff format --check . && uv run mypy src agents`
Expected: 오류 없음

- [ ] **Step 5: 커밋**

```bash
git add src/adk_study/testing.py tests/test_testing.py
git commit -m "feat(testing): add FakeLlm and run_turn helpers" -m "GPT 호출 없이 이벤트 흐름을 검증하려면 BaseLlm 을 바꿔 끼울 수 있어야
한다. Runner 는 그대로 쓰므로 함수 호출 이벤트와 최종 이벤트 순서가
실제와 같다."
```

---

### Task 4: 루트 README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: README 작성**

```markdown
# ADK 학습 프로젝트

Google ADK(Agent Development Kit) 1.36.x의 핵심 개념을 토픽 하나씩 최소 구현에서 출발해 단계적으로 확장하며 익힌다.
모든 단계는 `adk web`에서 선택해 실행할 수 있고, 각 단계의 차이는 커밋 diff 하나로 읽을 수 있다.

## 준비

```bash
uv sync
cp .env.example .env   # OPENAI_API_KEY 를 채운다
```

## 실행

```bash
uv run adk web agents
```

브라우저에서 http://127.0.0.1:8000 을 열고 왼쪽 위 드롭다운에서 단계를 고른다.
드롭다운은 알파벳순이므로 학습 순서는 아래 표를 따른다.

## 학습 순서

| 순서 | 토픽 | 단계 폴더 |
|---|---|---|
| 1 | basics | basics_01_hello, basics_02_tool |

토픽이 머지될 때마다 이 표에 줄을 더한다.

## 검사

```bash
uv run ruff check . && uv run ruff format --check .
uv run mypy src agents
uv run pytest
```

## 규칙

프로젝트 규칙은 /Users/randy/study/google-adk/CLAUDE.md 에 있고 설계는 /Users/randy/study/google-adk/docs/superpowers/specs/2026-09-07-adk-study-design.md 에 있다.
```

- [ ] **Step 2: 커밋**

```bash
git add README.md
git commit -m "docs: write root README with setup and study order" -m "드롭다운이 알파벳순이라 학습 순서를 따로 안내해야 한다. 토픽이 머지될
때마다 표에 줄을 더하는 방식으로 유지한다."
```

---

### Task 5: 브랜치 생성과 basics_01_hello

**Files:**
- Create: `agents/basics_01_hello/__init__.py`
- Create: `agents/basics_01_hello/agent.py`
- Create: `agents/basics_01_hello/README.md`
- Test: `tests/test_basics_01_hello.py`

**Interfaces:**
- Consumes: `adk_study.models.make_model`, `adk_study.testing.FakeLlm`, `text_reply`, `run_turn`
- Produces: `agents.basics_01_hello.agent.root_agent: LlmAgent` (name `hello`)

- [ ] **Step 1: 브랜치 생성**

```bash
git checkout -b feature/basics
```

- [ ] **Step 2: 실패하는 테스트 작성**

`tests/test_basics_01_hello.py`:

```python
"""basics_01_hello: instruction 만 있는 최소 에이전트."""

from agents.basics_01_hello.agent import root_agent
from adk_study.testing import FakeLlm, run_turn, text_reply


async def test_hello_returns_model_text_as_final_event():
    fake = FakeLlm(replies=[text_reply("안녕하세요, 반가워요")])
    root_agent.model = fake

    events = await run_turn(root_agent, "안녕")

    assert events[-1].author == "hello"
    assert events[-1].is_final_response()
    assert events[-1].content.parts[0].text == "안녕하세요, 반가워요"


async def test_instruction_is_sent_as_system_instruction():
    fake = FakeLlm(replies=[text_reply("네")])
    root_agent.model = fake

    await run_turn(root_agent, "안녕")

    system = fake.requests[0].config.system_instruction
    assert "한국어" in str(system)
```

- [ ] **Step 3: 실패 확인**

Run: `uv run pytest tests/test_basics_01_hello.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'agents.basics_01_hello'`

- [ ] **Step 4: 에이전트 구현**

`agents/basics_01_hello/__init__.py`:

```python
from . import agent
```

`agents/basics_01_hello/agent.py`:

```python
"""basics_01_hello: instruction 만 있는 최소 LlmAgent."""

from google.adk.agents import LlmAgent

from adk_study.models import make_model

root_agent = LlmAgent(
    name="hello",
    model=make_model(),
    description="인사만 하는 최소 에이전트",
    instruction="사용자에게 한국어로 짧고 친절하게 인사한다.",
)
```

- [ ] **Step 5: 통과 확인**

Run: `uv run pytest tests/test_basics_01_hello.py -v`
Expected: 2 passed

Run: `uv run ruff check . && uv run ruff format --check . && uv run mypy src agents`
Expected: 오류 없음

- [ ] **Step 6: adk web에서 확인**

Run: `uv run adk web agents` (백그라운드로 띄운 뒤 `curl -s http://127.0.0.1:8000/list-apps`)
Expected: 응답에 `"basics_01_hello"` 포함. 확인 후 프로세스를 종료한다.

- [ ] **Step 7: README 작성**

`agents/basics_01_hello/README.md`:

```markdown
# basics_01_hello

## 이 단계가 보여주는 것

- LlmAgent 하나가 에이전트의 최소 단위다.
  name, model, instruction 세 가지면 adk web 에서 대화할 수 있다.
- `root_agent` 라는 변수명과 `__init__.py` 의 `from . import agent` 가 adk web 이 에이전트를 찾는 약속이다.
- 모델은 `adk_study.models.make_model()` 이 `.env` 의 MODEL_NAME 으로 만든다.

## adk web 에서 확인할 것

- 드롭다운에서 basics_01_hello 를 고르고 인사를 보낸다.
- 오른쪽 Events 탭에 사용자 메시지 이벤트와 모델 응답 이벤트가 하나씩 생긴다.

## 이전 단계와 다른 점

첫 단계다.
```

- [ ] **Step 8: 커밋**

```bash
git add agents/basics_01_hello tests/test_basics_01_hello.py
git commit -m "feat(basics): add basics_01_hello minimal LlmAgent" -m "모든 토픽이 여기서 출발한다. instruction 만 있는 에이전트로 adk web 이
폴더를 인식하는 약속(root_agent, __init__.py)과 이벤트 두 개가 생기는
최소 흐름만 보여준다."
```

---

### Task 6: basics_02_tool 복사 커밋

**Files:**
- Create: `agents/basics_02_tool/` (basics_01_hello 복사)
- Create: `tests/test_basics_02_tool.py` (test_basics_01_hello.py 복사)

- [ ] **Step 1: 복사**

```bash
cp -r agents/basics_01_hello agents/basics_02_tool
cp tests/test_basics_01_hello.py tests/test_basics_02_tool.py
```

- [ ] **Step 2: 식별자만 교체**

`agents/basics_02_tool/agent.py`의 독스트링 첫 줄을 `"""basics_02_tool: instruction 만 있는 최소 LlmAgent."""`로, `name="hello"`를 `name="dice"`로 바꾼다.
`agents/basics_02_tool/README.md`의 제목을 `# basics_02_tool`로 바꾼다.
`tests/test_basics_02_tool.py`의 import를 `from agents.basics_02_tool.agent import root_agent`로, 첫 줄 독스트링을 `"""basics_02_tool: 도구 하나를 가진 에이전트."""`로, `author == "hello"`를 `author == "dice"`로 바꾼다.

- [ ] **Step 3: 통과 확인**

Run: `uv run pytest tests/test_basics_02_tool.py -v`
Expected: 2 passed

Run: `uv run ruff check . && uv run ruff format --check .`
Expected: 오류 없음

- [ ] **Step 4: 커밋**

```bash
git add agents/basics_02_tool tests/test_basics_02_tool.py
git commit -m "copy: basics_01_hello -> basics_02_tool" -m "다음 커밋의 diff 에 도구 추가만 남기기 위해 이전 단계를 그대로 복사한다.
바꾼 것은 폴더명, 에이전트 name, 독스트링 제목뿐이다."
```

---

### Task 7: basics_02_tool 수정 커밋

**Files:**
- Modify: `agents/basics_02_tool/agent.py`
- Modify: `agents/basics_02_tool/README.md`
- Modify: `tests/test_basics_02_tool.py`

**Interfaces:**
- Consumes: `call_reply`, `text_reply`, `FakeLlm`, `run_turn`
- Produces: `agents.basics_02_tool.agent.roll_die(sides: int) -> int`, `root_agent` (name `dice`)

- [ ] **Step 1: 실패하는 테스트 추가**

`tests/test_basics_02_tool.py`에 import를 바꾸고 테스트를 덧붙인다.

```python
from agents.basics_02_tool.agent import roll_die, root_agent
from adk_study.testing import FakeLlm, call_reply, run_turn, text_reply


def test_roll_die_stays_in_range():
    for _ in range(50):
        assert 1 <= roll_die(6) <= 6


async def test_tool_call_produces_call_and_response_events():
    fake = FakeLlm(
        replies=[call_reply("roll_die", {"sides": 6}), text_reply("굴렸어요")]
    )
    root_agent.model = fake

    events = await run_turn(root_agent, "주사위 굴려")

    assert events[0].get_function_calls()[0].name == "roll_die"
    result = events[1].get_function_responses()[0].response["result"]
    assert 1 <= result <= 6
    assert events[2].is_final_response()


async def test_tool_schema_is_sent_to_model():
    fake = FakeLlm(replies=[text_reply("네")])
    root_agent.model = fake

    await run_turn(root_agent, "안녕")

    assert "roll_die" in fake.requests[0].tools_dict
```

- [ ] **Step 2: 실패 확인**

Run: `uv run pytest tests/test_basics_02_tool.py -v`
Expected: FAIL, `ImportError: cannot import name 'roll_die'`

- [ ] **Step 3: 도구 추가**

`agents/basics_02_tool/agent.py`:

```python
"""basics_02_tool: 파이썬 함수 하나를 도구로 가진 LlmAgent."""

import random

from google.adk.agents import LlmAgent

from adk_study.models import make_model


def roll_die(sides: int) -> int:
    """sides 면 주사위를 한 번 굴려 나온 눈을 돌려준다.

    Args:
        sides: 주사위 면의 수.
    """
    return random.randint(1, sides)


root_agent = LlmAgent(
    name="dice",
    model=make_model(),
    description="주사위를 굴려 주는 에이전트",
    instruction="사용자가 주사위를 원하면 roll_die 도구를 쓰고 결과를 "
    "한국어로 알려 준다.",
    tools=[roll_die],
)
```

- [ ] **Step 4: 통과 확인**

Run: `uv run pytest -v`
Expected: 모두 passed

Run: `uv run ruff check . && uv run ruff format --check . && uv run mypy src agents`
Expected: 오류 없음

- [ ] **Step 5: README 수정**

`agents/basics_02_tool/README.md`:

```markdown
# basics_02_tool

## 이 단계가 보여주는 것

- 파이썬 함수를 `tools=[roll_die]` 로 넘기면 ADK 가 FunctionTool 로 감싼다.
- 함수 이름, 타입 힌트, 독스트링이 그대로 모델에 보내는 도구 스키마가 된다.
  `Args:` 절의 설명이 매개변수 설명으로 들어간다.
- 모델이 도구를 부르면 이벤트가 셋 생긴다.
  function_call 이벤트, function_response 이벤트, 최종 텍스트 이벤트 순서다.

## adk web 에서 확인할 것

- "주사위 굴려 줘" 라고 보낸다.
- Events 탭에서 function_call 과 function_response 이벤트를 펼쳐 args 와 response 를 본다.
- 최종 이벤트만 채팅창에 텍스트로 나타난다.

## 이전 단계와 다른 점

basics_01_hello 에 roll_die 함수와 `tools=[roll_die]` 한 줄이 더해졌다.
```

- [ ] **Step 6: 커밋**

```bash
git add agents/basics_02_tool tests/test_basics_02_tool.py
git commit -m "feat(basics): add roll_die tool to basics_02_tool" -m "도구가 붙으면 이벤트가 셋으로 늘어나는 것이 event 토픽의 출발점이다.
함수 시그니처와 독스트링이 스키마가 되는 방식을 보여주려고 FunctionTool
을 직접 만들지 않고 함수를 그대로 넘긴다."
```

---

### Task 8: feature/basics 머지

- [ ] **Step 1: 전체 검사**

Run: `uv run pytest && uv run ruff check . && uv run ruff format --check . && uv run mypy src agents`
Expected: 모두 통과

- [ ] **Step 2: README 학습 순서 표 확인**

Task 4에서 이미 basics 줄을 넣었으므로 변경 없음을 확인한다.

- [ ] **Step 3: rebase 후 no-ff 머지**

```bash
git checkout feature/basics
git rebase main
git checkout main
git merge --no-ff feature/basics -m "merge: basics 토픽" -m "instruction 만 있는 최소 LlmAgent 와 파이썬 함수 도구 하나를 붙인 단계를
adk web 에서 선택할 수 있게 한다. 이후 모든 토픽은 basics_02_tool 을
복사해 출발한다."
git branch -d feature/basics
git log --oneline --graph | head -15
```

Expected: 머지 커밋이 맨 위에 있고 feature/basics 브랜치가 없다.
