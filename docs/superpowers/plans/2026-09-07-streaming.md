# streaming 토픽 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** feature/streaming 브랜치에서 스트리밍과 비스트리밍의 차이를 세 단계로 보여주고, 리뷰 뒤 main 에 머지하고 푸시한다.

**Architecture:** runner 토픽의 main.py 구조를 이어받아 `run(agent, text, *, streaming)` 이 RunConfig 의 streaming_mode 를 바꾼다.
테스트용으로 조각을 partial 응답으로 내보내는 FakeStreamLlm 을 `adk_study.testing` 에 더한다.
streaming_01 은 SSE 조각 출력, streaming_02 는 두 모드 비교, streaming_03 은 도구 호출과 조각의 순서다.

**Tech Stack:** google-adk 1.36.2 RunConfig, StreamingMode.SSE, Event.partial, pytest capsys

**Spec:** /Users/randy/study/google-adk/docs/superpowers/specs/2026-09-07-adk-study-design.md

## Global Constraints

- 단계 폴더는 `agents/` 바로 아래에 `<토픽>_<두자리 번호>_<이름>` 형식으로 평평하게 둔다.
- 단계 추가는 복사 커밋 뒤 수정 커밋으로 나눈다. 복사 커밋 제목은 `copy: <이전> -> <새>` 형식이다.
- 수정 커밋의 Python 코드 변경량은 30줄을 목표로 한다. 복사, README, 테스트는 세지 않는다.
- 커밋 제목은 영어 50자 이내, 본문은 한글이다. Claude나 Anthropic 관련 trailer를 넣지 않는다.
- 주석, 독스트링, README는 한글이고 식별자는 영어다. Python 코드는 79자, 주석과 독스트링은 72자 이내다.
- 모든 커밋에서 `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src agents`가 통과한다. 검사 명령은 파이프 없이 실행해 종료 코드가 가려지지 않게 한다.
- 구현이 끝나면 CLAUDE.md 의 단계 리뷰 규칙대로 단계마다 리뷰 서브에이전트를 보낸 뒤 머지하고 `git push origin main` 한다.

## 1.36.2에서 확인한 사실

- `RunConfig(streaming_mode=StreamingMode.SSE)` 를 주면 LlmFlow 가 모델의 `generate_content_async(..., stream=True)` 를 부르고, 모델이 내는 `partial=True` 응답을 그대로 이벤트로 yield 한다. `StreamingMode.NONE`(기본) 에서는 partial 응답을 걸러 최종 응답만 yield 한다.
- LiteLlm 은 스트리밍 시 텍스트 조각마다 `partial=True` 응답을 내고, 마지막에 전체 텍스트를 합친 `partial=False` 응답을 낸다. 도구 호출은 조각을 모아 한 번에 non-partial 응답으로 낸다.
- Runner 는 `partial=True` 이벤트를 세션에 저장하지 않는다. 그래서 SSE 로 조각 3개와 최종 1개가 나와도 세션에는 최종 이벤트 하나만 남는다.
- partial 이벤트의 `is_final_response()` 는 False 다.
- 도구 호출과 스트리밍이 섞이면 이벤트 순서는 function_call(non-partial), function_response, 텍스트 조각들(partial), 최종 텍스트다. 세션에는 셋만 저장된다.
- adk web 은 요청 본문의 `streaming: true` 로 SSE 를 켠다. 웹 UI 의 토큰 스트리밍 토글이 이 값을 보낸다.
- 테스트용 모델은 `generate_content_async(llm_request, stream)` 에서 stream 이 True 일 때만 partial 응답을 내고, 마지막에 non-partial 전체 응답을 내면 된다.

---

### Task 1: 브랜치 생성과 FakeStreamLlm

**Files:**
- Modify: `src/adk_study/testing.py`
- Modify: `tests/test_testing.py`

**Interfaces:**
- Produces: `FakeStreamLlm(replies=[...])`. replies 원소가 `list[str]` 이면 stream=True 일 때 조각마다 partial 응답을 내고 마지막에 합친 응답을 낸다. 원소가 `types.Content` 면 한 번에 non-partial 로 낸다.

- [ ] **Step 1: 브랜치 생성**

```bash
git checkout -b feature/streaming
```

- [ ] **Step 2: 실패하는 테스트 추가**

`tests/test_testing.py` 끝에 덧붙이고 import 에 `FakeStreamLlm` 과 `from google.adk.agents.run_config import RunConfig, StreamingMode` 를 추가한다.

```python
async def test_fake_stream_llm_yields_chunks_only_in_sse_mode():
    fake = FakeStreamLlm(replies=[["안녕", "하세요"]])
    agent = LlmAgent(name="t", model=fake, instruction="")
    runner = InMemoryRunner(agent=agent, app_name="test")
    session = await runner.session_service.create_session(
        app_name="test", user_id="user"
    )
    message = types.Content(
        role="user", parts=[types.Part.from_text(text="hi")]
    )

    events = [
        e
        async for e in runner.run_async(
            user_id="user",
            session_id=session.id,
            new_message=message,
            run_config=RunConfig(streaming_mode=StreamingMode.SSE),
        )
    ]

    assert [(e.content.parts[0].text, e.partial) for e in events] == [
        ("안녕", True),
        ("하세요", True),
        ("안녕하세요", False),
    ]


async def test_fake_stream_llm_answers_whole_in_none_mode():
    fake = FakeStreamLlm(replies=[["안녕", "하세요"]])
    agent = LlmAgent(name="t", model=fake, instruction="")

    events = await run_turn(agent, "hi")

    assert [e.content.parts[0].text for e in events] == ["안녕하세요"]
```

`from google.genai import types` 도 import 한다.

- [ ] **Step 3: 실패 확인**

Run: `uv run pytest tests/test_testing.py -q`
Expected: FAIL, `ImportError: cannot import name 'FakeStreamLlm'`

- [ ] **Step 4: 구현**

`src/adk_study/testing.py` 의 FakeLlm 뒤에 추가한다.

```python
class FakeStreamLlm(BaseLlm):
    """조각 목록은 스트리밍으로, Content 는 한 번에 돌려준다.

    replies 원소가 list[str] 이면 stream=True 일 때 조각마다
    partial=True 응답을 내고 마지막에 합친 응답을 낸다. stream=False
    면 합친 응답만 낸다. 원소가 Content 면 partial 없이 그대로 낸다.
    LiteLlm 이 스트리밍할 때 내는 응답 순서와 같다.
    """

    model: str = "fake-stream"
    replies: list[list[str] | types.Content]
    requests: list[LlmRequest] = Field(default_factory=list)

    async def generate_content_async(
        self, llm_request: LlmRequest, stream: bool = False
    ) -> AsyncGenerator[LlmResponse]:
        self.requests.append(llm_request)
        reply = self.replies.pop(0)
        if isinstance(reply, types.Content):
            yield LlmResponse(content=reply)
            return
        if stream:
            for chunk in reply:
                yield LlmResponse(content=text_reply(chunk), partial=True)
        yield LlmResponse(content=text_reply("".join(reply)))
```

`text_reply` 가 FakeStreamLlm 보다 뒤에 정의되어 있으면 함수 호출 시점에만 쓰이므로 그대로 두어도 된다.

- [ ] **Step 5: 통과 확인과 커밋**

Run: `uv run pytest -q; uv run ruff check .; uv run ruff format --check .; uv run mypy src agents`
Expected: 모두 통과

```bash
git add src/adk_study/testing.py tests/test_testing.py
git commit -m "feat(testing): add FakeStreamLlm for partial responses" -m "스트리밍 단계를 모델 호출 없이 검증하려면 stream 인자에 따라 partial
응답을 내는 가짜 모델이 필요하다. LiteLlm 이 조각 뒤에 합친 응답을 내는
순서를 그대로 따라 실제 동작과 이벤트 순서가 같게 한다."
```

---

### Task 2: streaming_01_sse 복사 커밋

**Files:**
- Create: `agents/streaming_01_sse/` (runner_01_minimal 복사)
- Create: `tests/test_streaming_01_sse.py` (test_runner_01_minimal.py 복사)

- [ ] **Step 1: 복사와 식별자 교체**

```bash
cp -r agents/runner_01_minimal agents/streaming_01_sse
rm -rf agents/streaming_01_sse/__pycache__ agents/streaming_01_sse/.adk
cp tests/test_runner_01_minimal.py tests/test_streaming_01_sse.py
```

agent.py 독스트링 접두어와 `name="stream_tool"`, main.py 독스트링 접두어와 실행 명령의 모듈 경로와 `APP_NAME = "streaming_01_sse"`, README 제목, 테스트의 import 두 줄과 `"runner_tool"`, `[runner_tool]`, `APP_NAME == "streaming_01_sse"` 를 바꾼다. 독스트링은 첫 줄의 접두어(`"""runner_01_minimal:`)만 바꾸고 나머지는 그대로 둔다.

- [ ] **Step 2: 확인과 커밋**

Run: `uv run pytest tests/test_streaming_01_sse.py -q; uv run ruff check .; uv run ruff format --check .`
Expected: 통과. 테스트가 실패하면 식별자 치환이 빠진 곳을 고친 뒤 커밋한다.

```bash
git add agents/streaming_01_sse tests/test_streaming_01_sse.py
git commit -m "copy: runner_01_minimal -> streaming_01_sse" -m "스트리밍은 RunConfig 로 켜므로 Runner 를 직접 만드는 runner_01 을
복사한다."
```

---

### Task 3: streaming_01_sse 수정 커밋

**Files:**
- Modify: `agents/streaming_01_sse/main.py`
- Modify: `agents/streaming_01_sse/README.md`
- Modify: `tests/test_streaming_01_sse.py`

**Interfaces:**
- Produces: `run(agent, text, *, streaming: bool = True) -> list[Event]`. partial 이벤트는 텍스트를 줄바꿈 없이 이어서 출력하고, 최종 이벤트는 줄을 바꾼 뒤 `describe` 로 한 줄 출력한다.

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/test_streaming_01_sse.py` 전체:

```python
"""streaming_01_sse: SSE 모드에서 partial 이벤트를 조각으로 받는다."""

from adk_study.testing import FakeStreamLlm
from agents.streaming_01_sse.agent import root_agent
from agents.streaming_01_sse.main import APP_NAME, run


def chunked_answer() -> FakeStreamLlm:
    return FakeStreamLlm(replies=[["안녕", "하세", "요"]])


async def test_sse_yields_partials_then_final():
    root_agent.model = chunked_answer()

    events = await run(root_agent, "인사해 줘", streaming=True)

    assert [(e.content.parts[0].text, e.partial) for e in events] == [
        ("안녕", True),
        ("하세", True),
        ("요", True),
        ("안녕하세요", False),
    ]
    assert [e.is_final_response() for e in events] == [
        False,
        False,
        False,
        True,
    ]


async def test_none_mode_yields_only_final():
    root_agent.model = chunked_answer()

    events = await run(root_agent, "인사해 줘", streaming=False)

    assert [(e.content.parts[0].text, e.partial) for e in events] == [
        ("안녕하세요", None),
    ]


async def test_partials_are_printed_inline_then_final_line(capsys):
    root_agent.model = chunked_answer()

    await run(root_agent, "인사해 줘", streaming=True)

    out = capsys.readouterr().out
    assert out.startswith("안녕하세요\n")
    assert "[stream_tool] text 안녕하세요" in out


async def test_all_events_share_one_invocation():
    root_agent.model = chunked_answer()

    events = await run(root_agent, "인사해 줘", streaming=True)

    assert len({e.invocation_id for e in events}) == 1


def test_app_name_matches_folder():
    assert APP_NAME == "streaming_01_sse"
```

- [ ] **Step 2: 실패 확인**

Run: `uv run pytest tests/test_streaming_01_sse.py -q`
Expected: FAIL, `TypeError: run() got an unexpected keyword argument 'streaming'`

- [ ] **Step 3: main.py 수정**

`agents/streaming_01_sse/main.py` 의 모듈 독스트링을 다음으로 바꾼다.

```python
"""streaming_01_sse: SSE 모드에서 partial 이벤트를 조각으로 받는다.

RunConfig(streaming_mode=StreamingMode.SSE) 를 주면 모델이 내는
텍스트 조각이 partial=True 이벤트로 하나씩 온다. 마지막에 전체
텍스트를 담은 partial=False 이벤트가 오고 세션에는 그것만 남는다.

실행: uv run python -m agents.streaming_01_sse.main [메시지]
"""
```

import 에 `from google.adk.agents.run_config import RunConfig, StreamingMode` 를 추가하고 `run` 을 다음으로 바꾼다.

```python
async def run(
    agent: BaseAgent, text: str, *, streaming: bool = True
) -> list[Event]:
    """세션 하나를 만들고 메시지 한 개를 보내 이벤트를 출력하고 모은다.

    streaming 이 True 면 SSE 모드라 partial 이벤트가 조각으로 오고,
    False 면 NONE 모드라 최종 이벤트만 온다.
    """
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
    mode = StreamingMode.SSE if streaming else StreamingMode.NONE
    events: list[Event] = []
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=session.id,
        new_message=message,
        run_config=RunConfig(streaming_mode=mode),
    ):
        if event.partial:
            print(event.content.parts[0].text, end="", flush=True)
        else:
            print()
            print(describe(event))
        events.append(event)
    return events
```

`if __name__ == "__main__":` 블록의 기본 메시지를 `"자기소개를 세 문장으로 해 줘"` 로 바꾼다.

- [ ] **Step 4: 통과 확인**

Run: `uv run pytest -q; uv run ruff check .; uv run ruff format --check .; uv run mypy src agents`
Expected: 모두 통과. mypy 가 `content.parts` 의 Optional 을 지적하면 `describe` 와 같은 방식으로 가드한다.

- [ ] **Step 5: README 작성**

`agents/streaming_01_sse/README.md`:

```markdown
# streaming_01_sse

## 이 단계가 보여주는 것

- 스트리밍은 에이전트 설정이 아니라 한 턴의 RunConfig 로 켠다.
  `RunConfig(streaming_mode=StreamingMode.SSE)` 를 run_async 에 넘긴다.
- SSE 모드에서는 모델이 텍스트를 만드는 동안 조각마다 `partial=True` 이벤트가 온다.
  마지막에 조각을 모두 합친 텍스트가 `partial=False` 이벤트로 온다.
- partial 이벤트는 `is_final_response()` 가 False 이고 Runner 가 세션에 저장하지 않는다.
  세션에는 최종 이벤트 하나만 남으므로 다음 턴의 모델 입력은 스트리밍 여부와 무관하다.
- 기본값 `StreamingMode.NONE` 에서는 LlmFlow 가 partial 응답을 걸러 최종 이벤트만 yield 한다.
  같은 모델이라도 for 루프에 나오는 이벤트 수가 달라진다.
- 스크립트는 partial 이벤트의 텍스트를 줄바꿈 없이 이어 찍고, 최종 이벤트는 한 줄로 요약한다.

## adk web 에서 확인할 것

- 스크립트를 실행하면 글자가 조금씩 찍히다가 마지막에 `[stream_tool] text ...` 한 줄이 나온다.
- adk web 은 오른쪽 위 설정에서 토큰 스트리밍을 켜면 요청에 `streaming: true` 를 실어 같은 SSE 모드로 돈다.
  Events 탭에는 최종 이벤트만 남는다. partial 이벤트는 세션에 저장되지 않기 때문이다.

## 이전 단계와 다른 점

runner_01_minimal 의 run 에 streaming 인자가 생기고 run_async 에 RunConfig 를 넘긴다.
partial 이벤트를 구분해 출력하는 분기가 더해졌다.
```

- [ ] **Step 6: 커밋**

```bash
git add agents/streaming_01_sse tests/test_streaming_01_sse.py
git commit -m "feat(streaming): stream partial events with SSE mode" -m "스트리밍이 에이전트가 아니라 한 턴의 RunConfig 에 속한다는 점과, partial
이벤트가 세션에 남지 않는다는 점을 보인다. 같은 가짜 모델로 SSE 와
NONE 의 이벤트 수 차이를 검증한다."
```

---

### Task 4: streaming_02_compare 복사 커밋

**Files:**
- Create: `agents/streaming_02_compare/` (streaming_01_sse 복사)
- Create: `tests/test_streaming_02_compare.py`

- [ ] **Step 1: 복사와 식별자 교체**

```bash
cp -r agents/streaming_01_sse agents/streaming_02_compare
rm -rf agents/streaming_02_compare/__pycache__ agents/streaming_02_compare/.adk
cp tests/test_streaming_01_sse.py tests/test_streaming_02_compare.py
```

agent.py 독스트링 접두어와 `name="stream_compare"`, main.py 독스트링 접두어와 모듈 경로와 `APP_NAME = "streaming_02_compare"`, README 제목, 테스트의 import 와 `[stream_tool]`, `APP_NAME == "streaming_02_compare"` 를 바꾼다.

- [ ] **Step 2: 확인과 커밋**

Run: `uv run pytest tests/test_streaming_02_compare.py -q; uv run ruff check .; uv run ruff format --check .`

```bash
git add agents/streaming_02_compare tests/test_streaming_02_compare.py
git commit -m "copy: streaming_01_sse -> streaming_02_compare" -m "다음 커밋의 diff 에 두 모드를 나란히 돌리는 변경만 남기기 위해 이전
단계를 그대로 복사한다."
```

---

### Task 5: streaming_02_compare 수정 커밋

**Files:**
- Modify: `agents/streaming_02_compare/main.py`
- Modify: `agents/streaming_02_compare/README.md`
- Modify: `tests/test_streaming_02_compare.py`

**Interfaces:**
- Produces: `compare(agent, text) -> dict[str, int]`. 같은 메시지를 NONE 과 SSE 로 한 번씩 돌려 `{"none": 이벤트 수, "sse": 이벤트 수}` 를 돌려주고 각 모드의 이벤트 수와 세션에 저장된 이벤트 수를 출력한다.
- `run` 은 `session_service` 를 돌려주지 않으므로 `compare` 안에서 세션 서비스를 직접 만들어 저장 수를 센다. 이를 위해 `run` 에 `session_service: BaseSessionService | None = None` 인자를 더한다.

- [ ] **Step 1: 실패하는 테스트 추가**

`tests/test_streaming_02_compare.py` 에 덧붙인다. import 에 `compare` 를 추가한다.

```python
async def test_compare_counts_events_of_both_modes():
    root_agent.model = FakeStreamLlm(
        replies=[["안녕", "하세", "요"], ["안녕", "하세", "요"]]
    )

    counts = await compare(root_agent, "인사해 줘")

    assert counts == {"none": 1, "sse": 4}


async def test_compare_reports_same_stored_count(capsys):
    root_agent.model = FakeStreamLlm(
        replies=[["안녕", "하세", "요"], ["안녕", "하세", "요"]]
    )

    await compare(root_agent, "인사해 줘")

    out = capsys.readouterr().out
    assert "none: events=1 stored=2" in out
    assert "sse: events=4 stored=2" in out
```

- [ ] **Step 2: 실패 확인**

Run: `uv run pytest tests/test_streaming_02_compare.py -q`
Expected: FAIL, `ImportError: cannot import name 'compare'`

- [ ] **Step 3: main.py 수정**

`run` 시그니처를 다음으로 바꾸고 본문의 `session_service = InMemorySessionService()` 를 `session_service = session_service or InMemorySessionService()` 로 바꾼다. import 에 `from google.adk.sessions import BaseSessionService` 를 추가한다.

```python
async def run(
    agent: BaseAgent,
    text: str,
    *,
    streaming: bool = True,
    session_service: BaseSessionService | None = None,
) -> list[Event]:
```

`run` 뒤에 추가한다.

```python
async def compare(agent: BaseAgent, text: str) -> dict[str, int]:
    """같은 메시지를 NONE 과 SSE 로 돌려 이벤트 수를 비교한다.

    루프에 나온 이벤트 수는 다르지만 세션에 저장된 이벤트 수는 같다.
    """
    counts: dict[str, int] = {}
    for name, streaming in (("none", False), ("sse", True)):
        session_service = InMemorySessionService()
        events = await run(
            agent, text, streaming=streaming, session_service=session_service
        )
        listed = await session_service.list_sessions(
            app_name=APP_NAME, user_id=USER_ID
        )
        session = await session_service.get_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=listed.sessions[0].id,
        )
        stored = len(session.events) if session else 0
        print(f"{name}: events={len(events)} stored={stored}")
        counts[name] = len(events)
    return counts
```

모듈 독스트링을 다음으로 바꾸고 `if __name__ == "__main__":` 에서 `run` 대신 `compare(root_agent, ...)` 를 부른다.

```python
"""streaming_02_compare: NONE 과 SSE 를 같은 메시지로 비교한다.

루프에 나오는 이벤트 수는 모드에 따라 다르지만 세션에 저장되는
이벤트 수는 같다. 스트리밍은 전달 방식의 차이일 뿐 대화 기록을 바꾸지
않는다.

실행: uv run python -m agents.streaming_02_compare.main [메시지]
"""
```

- [ ] **Step 4: 통과 확인**

Run: `uv run pytest -q; uv run ruff check .; uv run ruff format --check .; uv run mypy src agents`
Expected: 모두 통과

- [ ] **Step 5: README 작성**

`agents/streaming_02_compare/README.md`:

```markdown
# streaming_02_compare

## 이 단계가 보여주는 것

- 같은 에이전트, 같은 메시지를 NONE 과 SSE 로 한 번씩 돌린다.
  루프에 나오는 이벤트는 NONE 이 1개, SSE 가 조각 수 더하기 1개다.
- 세션에 저장된 이벤트 수는 두 모드 모두 2개(사용자 메시지와 최종 응답)다.
  partial 이벤트는 저장되지 않으므로 스트리밍은 전달 방식의 차이일 뿐 대화 기록을 바꾸지 않는다.
- 모델 호출 횟수도 같다. SSE 는 한 번의 호출에서 응답이 여러 조각으로 나뉘어 올 뿐이다.
- 실제 GPT 를 부르면 SSE 의 첫 조각이 NONE 의 최종 응답보다 먼저 도착한다.
  사용자가 기다리는 시간이 줄어드는 것이 스트리밍의 목적이고, 전체 완료 시각은 비슷하다.

## adk web 에서 확인할 것

- 스크립트를 실행하면 두 모드의 결과가 차례로 찍히고 마지막에 `none: events=1 stored=2`, `sse: events=N stored=2` 가 나온다.
- adk web 에서 토큰 스트리밍을 켜고 끄며 같은 질문을 보낸다.
  화면에 글자가 나타나는 방식은 다르지만 Events 탭의 이벤트 수는 같다.

## 이전 단계와 다른 점

streaming_01_sse 의 run 에 session_service 인자가 생기고, 두 모드를 돌려 세는 compare 가 더해졌다.
```

- [ ] **Step 6: 커밋**

```bash
git add agents/streaming_02_compare tests/test_streaming_02_compare.py
git commit -m "feat(streaming): compare NONE and SSE event counts" -m "스트리밍이 전달 방식의 차이일 뿐 세션 기록을 바꾸지 않는다는 점을 두
모드를 나란히 돌려 숫자로 보인다."
```

---

### Task 6: streaming_03_tool 복사 커밋

**Files:**
- Create: `agents/streaming_03_tool/` (streaming_01_sse 복사)
- Create: `tests/test_streaming_03_tool.py`

- [ ] **Step 1: 복사와 식별자 교체**

```bash
cp -r agents/streaming_01_sse agents/streaming_03_tool
rm -rf agents/streaming_03_tool/__pycache__ agents/streaming_03_tool/.adk
cp tests/test_streaming_01_sse.py tests/test_streaming_03_tool.py
```

agent.py 독스트링 접두어와 `name="stream_with_tool"`, main.py 독스트링 접두어와 모듈 경로와 `APP_NAME = "streaming_03_tool"`, README 제목, 테스트의 import 와 `[stream_tool]`, `APP_NAME == "streaming_03_tool"` 를 바꾼다.

- [ ] **Step 2: 확인과 커밋**

Run: `uv run pytest tests/test_streaming_03_tool.py -q; uv run ruff check .; uv run ruff format --check .`

```bash
git add agents/streaming_03_tool tests/test_streaming_03_tool.py
git commit -m "copy: streaming_01_sse -> streaming_03_tool" -m "도구 호출과 조각의 순서만 보이면 되므로 compare 가 없는 streaming_01 을
복사한다."
```

---

### Task 7: streaming_03_tool 수정 커밋

**Files:**
- Modify: `agents/streaming_03_tool/main.py` (describe 의 partial 표시)
- Modify: `agents/streaming_03_tool/README.md`
- Modify: `tests/test_streaming_03_tool.py`

에이전트는 이미 count_chars 도구를 가지고 있다(runner_01 에서 물려받음). 이 단계는 도구 호출 턴을 SSE 로 돌렸을 때의 이벤트 순서를 테스트와 README 로 고정한다.

- [ ] **Step 1: 실패하는 테스트 추가**

`tests/test_streaming_03_tool.py` 에 덧붙인다. import 에 `call_reply` 와 `describe` 를 추가한다.

```python
def tool_then_chunks() -> FakeStreamLlm:
    """도구 호출 응답 뒤에 조각으로 된 최종 답이 온다."""
    return FakeStreamLlm(
        replies=[
            call_reply("count_chars", {"text": "안녕 하세요"}),
            ["5글", "자예", "요"],
        ]
    )


async def test_tool_call_is_never_partial():
    root_agent.model = tool_then_chunks()

    events = await run(root_agent, "글자 수 세 줘", streaming=True)

    kinds = [
        "call"
        if e.get_function_calls()
        else "response"
        if e.get_function_responses()
        else f"text:{e.partial}"
        for e in events
    ]
    assert kinds == [
        "call",
        "response",
        "text:True",
        "text:True",
        "text:True",
        "text:False",
    ]


async def test_only_non_partial_events_are_stored():
    root_agent.model = tool_then_chunks()

    events = await run(root_agent, "글자 수 세 줘", streaming=True)

    assert sum(1 for e in events if not e.partial) == 3


async def test_describe_marks_partial_events():
    root_agent.model = tool_then_chunks()
    events = await run(root_agent, "글자 수 세 줘", streaming=True)

    assert describe(events[2]) == "[stream_with_tool] partial 5글"
    assert describe(events[-1]) == "[stream_with_tool] text 5글자예요"
```

- [ ] **Step 2: 실패 확인**

Run: `uv run pytest tests/test_streaming_03_tool.py -q`
Expected: `test_describe_marks_partial_events` FAIL (describe 가 partial 을 text 로 표시)

- [ ] **Step 3: describe 수정**

`agents/streaming_03_tool/main.py` 의 `describe` 마지막 두 줄을 다음으로 바꾼다.

```python
    parts = event.content.parts if event.content else None
    text = parts[0].text if parts else ""
    kind = "partial" if event.partial else "text"
    return f"[{event.author}] {kind} {text}"
```

모듈 독스트링을 다음으로 바꾼다.

```python
"""streaming_03_tool: 도구 호출 턴을 SSE 로 돌렸을 때의 이벤트 순서.

도구 호출은 조각으로 오지 않는다. function_call 과 function_response
가 먼저 non-partial 로 오고, 그 결과를 본 모델의 답만 조각으로 온다.

실행: uv run python -m agents.streaming_03_tool.main [메시지]
"""
```

- [ ] **Step 4: 통과 확인**

Run: `uv run pytest -q; uv run ruff check .; uv run ruff format --check .; uv run mypy src agents`
Expected: 모두 통과. streaming_01 의 출력 테스트는 이 폴더와 무관하므로 그대로 통과한다.

- [ ] **Step 5: README 작성**

`agents/streaming_03_tool/README.md`:

```markdown
# streaming_03_tool

## 이 단계가 보여주는 것

- 도구 호출은 조각으로 오지 않는다.
  LiteLlm 은 스트리밍 중에도 function_call 조각을 모아 하나의 non-partial 응답으로 낸다.
  텍스트만 partial 이벤트로 흘러온다.
- 도구 턴의 SSE 이벤트 순서는 function_call, function_response, 텍스트 조각들, 최종 텍스트다.
  앞의 둘과 마지막 하나만 세션에 저장된다.
- 첫 모델 호출은 도구 호출로 끝나므로 조각이 없고, 두 번째 모델 호출의 답만 조각으로 온다.
  화면에 글자가 찍히기 전에 도구 실행이 끝나야 한다.
- describe 가 partial 이벤트를 `partial` 로 표시해 종류가 넷(function_call, function_response, partial, text)이 된다.

## adk web 에서 확인할 것

- 토큰 스트리밍을 켜고 "안녕 하세요 글자 수 세 줘" 를 보낸다.
- 도구 호출 표시가 먼저 나오고 그 뒤에 답이 글자 단위로 나타난다.
- Events 탭에는 사용자 메시지, function_call, function_response, 최종 응답 넷만 있다.

## 이전 단계와 다른 점

streaming_01_sse 의 describe 가 partial 을 구분한다.
에이전트와 도구는 그대로이고 테스트가 도구 턴의 순서를 고정한다.
```

- [ ] **Step 6: 커밋**

```bash
git add agents/streaming_03_tool tests/test_streaming_03_tool.py
git commit -m "feat(streaming): fix event order of a streamed tool turn" -m "도구 호출은 조각으로 오지 않고 텍스트만 partial 로 온다는 점을 순서로
고정한다. describe 가 partial 을 따로 표시해 스크립트 출력에서도 구분되게
한다."
```

---

### Task 8: 리뷰, README 갱신, 머지, 푸시

- [ ] **Step 1: 단계 리뷰**

CLAUDE.md 의 단계 리뷰 규칙대로 세 단계에 리뷰 서브에이전트를 병렬로 보낸다. main.py 도 리뷰 대상에 넣는다. 결과를 확인하고 단계마다 `docs(streaming): ...` 로 커밋한다.

- [ ] **Step 2: 표에 streaming 줄 추가**

runner 줄 아래에 넣는다.

```markdown
| 6 | streaming | streaming_01_sse, streaming_02_compare, streaming_03_tool |
```

```bash
git add README.md
git commit -m "docs: add streaming topic to study order" -m "머지 전에 학습 순서 표를 갱신해 드롭다운 알파벳순과 학습 순서를 잇는다."
```

- [ ] **Step 3: 전체 검사, 머지, 푸시**

```bash
git rebase main
git checkout main
git merge --no-ff feature/streaming -m "merge: streaming 토픽" -m "SSE 조각 출력, 두 모드 비교, 도구 턴의 순서 세 단계로 스트리밍이 전달
방식의 차이일 뿐 세션 기록을 바꾸지 않는다는 점을 보인다."
git branch -d feature/streaming
git push origin main
```
