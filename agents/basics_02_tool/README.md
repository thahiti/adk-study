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
