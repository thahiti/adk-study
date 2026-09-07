# event_02_function_call

## 이 단계가 보여주는 것

- 도구 호출 한 번은 이벤트 셋이 된다.
  1. function_call 이벤트: 모델이 도구를 부르겠다는 요청. content.role 은 model.
  2. function_response 이벤트: ADK 가 도구를 실행한 결과. author 는 에이전트 name 이지만 content.role 은 user 다.
     genai Content 의 role 은 user 와 model 둘뿐이고, 도구 결과는 모델이 만든 것이 아니라 모델에게 넣어 주는 입력이라 user 가 된다.
  3. 최종 텍스트 이벤트: 결과를 본 모델의 답.
- 도구를 실행하는 것은 모델이 아니라 ADK 다.
  모델은 이름과 인자만 돌려주고, ADK 가 파이썬 함수를 부른 뒤 결과를 function_response 로 만들어 모델을 다시 부른다.
  그래서 도구 턴에서는 모델이 두 번 불리고, 두 번째 호출의 대화 기록 끝에 role user 인 도구 결과가 붙는다.
- function_response 의 id 는 function_call 의 id 와 같다. 어느 호출의 결과인지 이 값으로 이어진다.
- 도구 함수가 dict 가 아닌 값을 돌려주면 ADK 가 `{"result": 값}` 으로 감싼다.
- 세 이벤트는 invocation_id 가 같다. 사용자 메시지 하나가 시작한 한 턴이다.
- `is_final_response()` 는 마지막 이벤트에서만 True 다.
  function_call 이나 function_response 가 들어 있으면 False 다.
  LlmFlow 는 True 인 이벤트가 나올 때까지 모델 호출을 반복하므로, 이 값이 턴을 이어갈지 끝낼지 정한다.
- `get_function_calls()` 와 `get_function_responses()` 로 parts 를 뒤지지 않고 꺼낼 수 있다.
- 일반 파이썬 함수를 tools 에 넣으면 FunctionTool 로 감싸진다.
  독스트링이 도구 설명, 타입 힌트가 인자 스키마가 되어 모델에 전달된다.

## adk web 에서 확인할 것

- "안녕 하세요 글자 수 세 줘" 라고 보낸다.
- Events 탭에 이벤트가 넷 있다. 사용자 메시지, function_call, function_response, 최종 응답 순서다.
- function_response 이벤트를 펼쳐 content.role 이 user 이고 response 가 `{"result": 5}` 인 것을 본다.
- function_call 과 function_response 의 id 가 같은 것을 본다.

## 이전 단계와 다른 점

event_01_text 에 count_chars 도구가 더해졌다.
이벤트가 하나에서 셋으로 늘어나고, 모델 호출은 한 번에서 두 번으로 늘어난다.
