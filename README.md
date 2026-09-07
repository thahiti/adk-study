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
| 2 | event | event_01_text, event_02_function_call, event_03_transfer, event_04_custom_event |
| 3 | state | state_01_output_key, state_02_tool_context, state_03_prefixes, state_04_sequential |
| 4 | session | session_01_inmemory, session_02_sqlite, session_03_include_contents, session_04_compaction |
| 5 | runner | runner_01_minimal, runner_02_services, runner_03_run_config |

토픽이 머지될 때마다 이 표에 줄을 더한다.

## 검사

```bash
uv run ruff check . && uv run ruff format --check .
uv run mypy src agents
uv run pytest
```

## 규칙

프로젝트 규칙은 /Users/randy/study/google-adk/CLAUDE.md 에 있고 설계는 /Users/randy/study/google-adk/docs/superpowers/specs/2026-09-07-adk-study-design.md 에 있다.
