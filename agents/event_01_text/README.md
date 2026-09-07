# event_01_text

## 이 단계가 보여주는 것

- Runner 와 에이전트 사이를 오가는 단위는 Event 다.
  모델이 텍스트로 답하면 Event 하나가 생긴다.
- `runner.run_async()` 가 밖으로 내보내는 것은 모델 쪽 이벤트뿐이다.
  사용자 메시지도 Event 로 만들어지지만 세션에 저장만 하고 내보내지 않는다.
  그래서 테스트에서는 이벤트가 하나이고 adk web 의 Events 탭에는 두 개가 보인다.
- Event 의 핵심 필드
  - id: 이벤트 고유 식별자. Event 를 만들 때 uuid 로 자동 채워진다.
  - invocation_id: 사용자 메시지 하나로 시작된 턴(invocation)의 식별자.
    Runner 가 턴을 시작할 때 "e-" 뒤에 uuid 를 붙여 만들고, 같은 턴의 이벤트는 모두 같은 값을 가진다.
  - author: 이벤트를 만든 주체. 사용자 메시지는 "user", 모델 응답은 "model" 이 아니라 에이전트 name 이다.
  - content: genai 의 Content. role 과 parts 를 가진다.
    role 은 대화에서 누가 말했는지("user" 또는 "model")이고, author 는 어느 에이전트가 만들었는지다.
    에이전트가 여럿이면 role 이 같아도 author 가 다르므로 두 축을 구분한다.
  - actions: 상태 변경, 에이전트 전환 같은 부수 효과. 이 단계에서는 모두 비어 있다.
  - partial: 스트리밍 조각이면 True. 스트리밍이 아니면 False 또는 None 이다.
    값은 모델 어댑터가 정한다. 테스트의 FakeLlm 은 건드리지 않아 기본값 None 이 남고, adk web 이 쓰는 LiteLlm 은 False 를 넣는다.
    ADK 는 두 값을 모두 "조각이 아님"으로 다룬다.
  - timestamp: 생성 시각(epoch 초). `time.time()` 값이다.
- `is_final_response()` 는 함수 호출 파트도 함수 응답 파트도 없고 partial 이 아닌 이벤트에서 True 다.
  텍스트만 있는 이 단계의 응답이 그 경우다.
  Runner 는 마지막 이벤트가 True 이면 모델 호출 루프를 끝내므로, 이 값이 턴의 종료 조건이다.

## adk web 에서 확인할 것

- 질문을 하나 보내고 Events 탭을 연다.
- 사용자 메시지 이벤트(author user)와 응답 이벤트(author event_text)가 하나씩 있고 invocation_id 가 같다.
- 응답 이벤트를 펼쳐 content.role 이 model 이고 actions 가 비어 있는지 본다.
- 응답 이벤트의 partial 이 false 인지 본다. 테스트의 None 과 다른 이유는 위 partial 설명에 있다.

## 이전 단계와 다른 점

basics_01_hello 와 코드는 같고 name, description, instruction 만 다르다.
학습 포인트는 테스트가 검사하는 Event 필드에 있다.
