# streaming_03_tool

## 이 단계가 보여주는 것

- 도구 호출은 조각으로 오지 않는다.
  LiteLlm 은 스트리밍 중에도 function_call 조각을 모아 하나의 non-partial 응답으로 낸다.
  텍스트만 partial 이벤트로 흘러온다.
- 도구 턴의 SSE 이벤트 순서는 function_call, function_response, 텍스트 조각들, 최종 텍스트다.
  앞의 둘과 마지막 하나만 세션에 저장된다.
- 첫 모델 호출은 도구 호출로 끝나므로 조각이 없고, 두 번째 모델 호출의 답만 조각으로 온다.
  화면에 글자가 찍히기 전에 도구 실행이 끝나야 한다.
- describe 가 partial 이벤트를 `partial` 로 표시해 종류가 넷(function_call, function_response, partial, text)이 된다.

## adk web 에서 확인할 것

- 토큰 스트리밍을 켜고 "안녕 하세요 글자 수 세 줘" 를 보낸다.
- 도구 호출 표시가 먼저 나오고 그 뒤에 답이 글자 단위로 나타난다.
- Events 탭에는 사용자 메시지, function_call, function_response, 최종 응답 넷만 있다.

## 이전 단계와 다른 점

streaming_01_sse 의 describe 가 partial 을 구분한다.
에이전트와 도구는 그대로이고 테스트가 도구 턴의 순서를 고정한다.
