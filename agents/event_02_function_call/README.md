# event_02_function_call

## 이 단계가 보여주는 것

- 도구 호출 한 번은 이벤트 셋이 된다.
  1. function_call 이벤트: 모델이 도구를 부르겠다는 요청. content.role 은 model.
  2. function_response 이벤트: ADK 가 도구를 실행한 결과. author 는 에이전트 name 이지만 content.role 은 user 다. 모델 입장에서는 사용자 쪽에서 온 입력이기 때문이다.
  3. 최종 텍스트 이벤트: 결과를 본 모델의 답.
- 세 이벤트는 invocation_id 가 같다. 사용자 메시지 하나가 시작한 한 턴이다.
- `is_final_response()` 는 마지막 이벤트에서만 True 다.
  function_call 이나 function_response 가 들어 있으면 False 다.
- `get_function_calls()` 와 `get_function_responses()` 로 parts 를 뒤지지 않고 꺼낼 수 있다.

## adk web 에서 확인할 것

- "안녕 하세요 글자 수 세 줘" 라고 보낸다.
- Events 탭에 이벤트가 넷 있다. 사용자 메시지, function_call, function_response, 최종 응답 순서다.
- function_response 이벤트를 펼쳐 content.role 이 user 인 것을 본다.
- 채팅창에는 최종 응답만 텍스트로 보인다.

## 이전 단계와 다른 점

event_01_text 에 count_chars 도구가 더해졌다.
이벤트가 하나에서 셋으로 늘어난다.
