# basics_01_hello

## 이 단계가 보여주는 것

- LlmAgent 하나가 에이전트의 최소 단위다.
  필수 필드는 name 뿐이고, name, model, instruction 세 가지면 adk web 에서 대화할 수 있다.
  model 을 비우면 ADK 기본값인 gemini-2.5-flash 를 쓴다.
- adk web 은 `agents/<폴더>/agent.py` 안의 `root_agent` 변수를 찾는다.
  폴더명이 드롭다운 이름이고 변수명 `root_agent` 는 바꿀 수 없다.
  `__init__.py` 의 `from . import agent` 는 ADK 예제가 따르는 관례로, 없어도 로더가 `agent.py` 를 직접 임포트한다.
- 모델은 `adk_study.models.make_model()` 이 `.env` 의 MODEL_NAME 으로 만든다.
  adk web 은 에이전트 폴더에서 위로 올라가며 `.env` 를 찾아 먼저 읽는다.
- instruction 은 모델 요청의 system_instruction 으로 매 턴 다시 보내진다.
  ADK 가 그 뒤에 name 과 description 으로 만든 문장을 덧붙이므로 description 도 모델이 읽는다.

## adk web 에서 확인할 것

- 드롭다운에서 basics_01_hello 를 고르고 인사를 보낸다.
- 오른쪽 Events 탭에 사용자 메시지 이벤트(author user)와 모델 응답 이벤트(author hello)가 하나씩 생긴다.
  사용자 이벤트는 Runner 가 세션에 저장만 하고 코드로 돌려주지는 않는다.
  테스트 `test_session_keeps_user_and_agent_events` 가 이 차이를 보여준다.
- 이벤트 안에 instruction 은 없다.
  instruction 은 세션에 저장되지 않고 요청마다 다시 붙는다.

## 이전 단계와 다른 점

첫 단계다.
