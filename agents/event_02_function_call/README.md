# event_02_function_call

## 이 단계가 보여주는 것

- Runner 와 에이전트 사이를 오가는 단위는 Event 다.
  모델이 텍스트로 답하면 Event 하나가 생긴다.
- Event 의 핵심 필드
  - id: 이벤트 고유 식별자
  - invocation_id: 사용자 메시지 하나로 시작된 턴의 식별자. 같은 턴의 이벤트는 모두 같은 값이다.
  - author: 이벤트를 만든 주체. 사용자 메시지는 "user", 모델 응답은 에이전트 name 이다.
  - content: genai 의 Content. role 과 parts 를 가진다.
  - actions: 상태 변경, 에이전트 전환 같은 부수 효과. 이 단계에서는 모두 비어 있다.
  - partial: 스트리밍 조각이면 True. 스트리밍이 아니면 None 이다.
  - timestamp: 생성 시각(epoch 초)
- `is_final_response()` 는 도구 호출이 섞이지 않은 텍스트 이벤트에서 True 다.

## adk web 에서 확인할 것

- 질문을 하나 보내고 Events 탭을 연다.
- 사용자 메시지 이벤트(author user)와 응답 이벤트(author event_text)가 하나씩 있고 invocation_id 가 같다.
- 응답 이벤트를 펼쳐 content.role 이 model 이고 actions 가 비어 있는지 본다.

## 이전 단계와 다른 점

basics_01_hello 와 코드는 같고 이름과 instruction 만 다르다.
학습 포인트는 테스트가 검사하는 Event 필드에 있다.
