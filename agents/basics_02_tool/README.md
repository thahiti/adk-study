# basics_02_tool

## 이 단계가 보여주는 것

- 파이썬 함수를 `tools=[roll_die]` 로 넘기면 ADK 가 요청을 만들 때 FunctionTool 로 감싼다.
  함수 이름이 도구 이름이 된다.
- 독스트링 전체가 도구 설명이 되고, 타입 힌트가 매개변수 스키마가 된다.
  1.36.2 는 `Args:` 절을 따로 해석하지 않는다.
  매개변수에는 타입만 들어가고 `Args:` 절은 도구 설명 문자열 안에 통째로 실려 간다.
  그래서 독스트링은 모델이 읽는 글이라 생각하고 쓴다.
- 도구가 dict 가 아닌 값을 돌려주면 ADK 가 `{"result": 값}` 으로 감싼다.
  function_response 의 response 가 이 모양이다.
- 모델이 도구를 부르면 한 턴에 모델을 두 번 부르고 이벤트가 셋 생긴다.
  function_call 이벤트, function_response 이벤트, 최종 텍스트 이벤트 순서다.
  ADK 가 도구를 실행한 뒤 그 결과를 대화에 붙여 모델을 다시 부르고, 그 답이 최종 텍스트다.
- 세 이벤트의 author 는 모두 에이전트 이름 `dice` 다.
  function_response 이벤트는 content.role 이 `user` 인데, 모델 입장에서 도구 결과는 밖에서 들어온 입력이기 때문이다.
- `is_final_response()` 는 function_call 과 function_response 이벤트에서 False 다.
  세 이벤트 중 최종 텍스트 이벤트만 True 다.

## adk web 에서 확인할 것

- "주사위 굴려 줘" 라고 보낸다.
- Events 탭에서 function_call 과 function_response 이벤트를 펼쳐 args 와 response 를 본다.
  response 가 `{"result": 눈}` 모양인지 본다.
- 채팅창에서 텍스트로 읽히는 것은 최종 이벤트뿐이다.
- "안녕" 처럼 주사위와 무관한 말을 보내면 도구를 부르지 않고 이벤트가 하나만 생긴다.

## 이전 단계와 다른 점

basics_01_hello 에 roll_die 함수와 `tools=[roll_die]` 한 줄이 더해졌다.
instruction 에 언제 도구를 쓸지도 적었다.
도구가 있다고 모델이 알아서 쓰지는 않기 때문이다.

테스트에서는 `call_reply` 로 모델이 도구 호출을 요청한 것처럼 꾸민다.
FakeLlm 에 응답을 두 개 주는 이유는 한 턴에 모델이 두 번 불리기 때문이다.
`fake.requests[0].tools_dict` 는 ADK 가 요청에 실은 도구를 이름으로 찾는 dict 다.
도구 호출이 오면 이 dict 에서 이름으로 찾아 실행한다.
