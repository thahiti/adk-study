# streaming_03_tool

## 이 단계가 보여주는 것

- 도구 호출은 조각으로 오지 않는다.
  LiteLlm 은 스트리밍 중에 텍스트 조각은 바로 partial 응답으로 내보내지만, function_call 조각은 이름과 인자가 다 모일 때까지 쌓아 두었다가 스트림이 끝난 뒤 하나의 non-partial 응답으로 낸다.
  인자가 JSON 문자열로 잘려서 오기 때문에 반쯤 온 인자로는 도구를 부를 수 없어서다.
- LlmFlow 도 partial 이벤트에 function_call 이 있으면 실행하지 않고 넘긴다.
  partial 이벤트는 세션에 저장되지 않으므로 거기서 도구를 실행하면 기록 없는 호출이 생기기 때문이다.
  도구 실행은 언제나 non-partial 이벤트에서만 일어난다.
- 도구 턴의 SSE 이벤트 순서는 function_call, function_response, 텍스트 조각들, 최종 텍스트다.
  앞의 둘과 마지막 하나만 세션에 저장되고, 사용자 메시지까지 더하면 세션에는 이벤트 넷이 남는다.
- 모델 호출은 두 번이다.
  첫 호출은 모델이 도구 호출만 내므로 조각 없이 function_call 이벤트 하나로 끝나고, 도구 결과를 본 두 번째 호출의 답만 조각으로 온다.
  그래서 화면에 글자가 찍히기 전에 도구 실행이 끝난다.
  모델이 도구 호출 앞에 텍스트를 함께 내면 그 텍스트는 조각으로 먼저 오고 function_call 이벤트에도 같이 실린다.
- describe 가 partial 이벤트를 `partial` 로 표시해 종류가 넷(function_call, function_response, partial, text)이 된다.

## adk web 에서 확인할 것

- 스크립트를 실행하면 `function_call count_chars {...}` 와 `function_response {'result': 5}` 두 줄이 먼저 찍힌 뒤 답이 조각으로 이어 찍히고, 마지막에 `[stream_with_tool] text ...` 한 줄이 나온다.
- adk web 에서 토큰 스트리밍을 켜고 "안녕 하세요 글자 수 세 줘" 를 보낸다.
  Events 탭에는 사용자 메시지, function_call, function_response, 최종 응답 넷만 있고, function_call 과 function_response 가 최종 응답보다 앞에 있다.

## 이전 단계와 다른 점

streaming_01_sse 의 describe 가 partial 을 구분한다.
에이전트와 도구는 그대로이고 테스트가 도구 턴의 순서와 세션에 남는 이벤트를 고정한다.
