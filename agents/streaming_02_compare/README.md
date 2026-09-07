# streaming_02_compare

## 이 단계가 보여주는 것

- 같은 에이전트, 같은 메시지를 NONE 과 SSE 로 한 번씩 돌린다.
  도구를 부르지 않는 메시지라면 루프에 나오는 이벤트는 NONE 이 1개, SSE 가 조각 수 더하기 1개다.
  도구를 부르면 function_call 과 function_response 이벤트가 두 모드 모두에 더해진다.
- 세션에 저장된 이벤트 수는 두 모드 모두 2개(사용자 메시지와 최종 응답)다.
  partial 이벤트는 저장되지 않으므로 스트리밍은 전달 방식의 차이일 뿐 대화 기록을 바꾸지 않는다.
- 모델 호출 횟수도 같다.
  LlmFlow 는 두 모드 모두 `generate_content_async` 를 한 번 부르고 `stream` 인자만 SSE 일 때 True 로 준다.
  테스트는 FakeStreamLlm 이 받은 요청 수로 이를 확인한다.
- 스트리밍의 목적은 모델이 답을 다 만들기 전에 첫 조각을 보여 주어 사용자가 기다리는 시간을 줄이는 것이다.
  이 스크립트는 시각을 재지 않으므로 실제 GPT 로 돌릴 때 화면에서 체감으로만 확인한다.
- run 은 루프에 나온 이벤트만 돌려주므로 저장된 이벤트를 세려면 세션 서비스를 밖에서 만들어 넘기고 나중에 조회해야 한다.
  session_service 인자가 생긴 이유다.
- `InMemorySessionService.list_sessions` 는 events 를 비운 세션 목록을 준다.
  그래서 compare 는 list_sessions 로 id 를 찾은 뒤 get_session 으로 다시 읽어 이벤트를 센다.

## adk web 에서 확인할 것

- 스크립트를 실행하면 두 모드의 결과가 차례로 찍히고 마지막에 `none: events=1 stored=2`, `sse: events=N stored=2` 가 나온다.
- adk web 에서 토큰 스트리밍을 켜고 끄며 같은 질문을 보낸다.
  화면에 글자가 나타나는 방식은 다르지만 Events 탭의 이벤트 수는 같다.

## 이전 단계와 다른 점

streaming_01_sse 의 run 에 session_service 인자가 생기고, 두 모드를 돌려 세는 compare 가 더해졌다.
compare 는 모드마다 세션 서비스를 새로 만들어 세션이 하나뿐이게 하고, 그 세션의 이벤트 수를 저장 수로 찍는다.
