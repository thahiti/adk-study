# basics_02_tool

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
