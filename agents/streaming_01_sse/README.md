# streaming_01_sse

## 이 단계가 보여주는 것

- 스트리밍은 에이전트 설정이 아니라 한 턴의 RunConfig 로 켠다.
  `RunConfig(streaming_mode=StreamingMode.SSE)` 를 run_async 에 넘긴다.
  adk web 도 같은 방식으로 켠다.
- SSE 모드에서는 모델이 텍스트를 만드는 동안 조각마다 `partial=True` 이벤트가 온다.
  마지막에 조각을 모두 합친 텍스트가 `partial=False` 이벤트로 온다.
  LiteLlm 이 이 순서대로 응답을 내고 LlmFlow 는 응답 하나를 이벤트 하나로 바꾼다.
- partial 이벤트는 `is_final_response()` 가 False 다.
  이 메서드가 function_call 과 function_response 가 없고 partial 이 아닐 때만 True 를 주기 때문이다.
- Runner 는 partial 이벤트를 세션에 저장하지 않는다.
  run_async 가 이벤트를 yield 하기 직전에 append_event 를 부르는데 partial 이면 건너뛴다.
  세션 서비스의 append_event 도 partial 이면 그냥 돌려보내므로 직접 불러도 저장되지 않는다.
  세션에는 최종 이벤트 하나만 남으므로 다음 턴의 모델 입력은 스트리밍 여부와 무관하다.
- 기본값 `StreamingMode.NONE` 에서는 LlmFlow 가 모델에 `stream=False` 를 넘긴다.
  LiteLlm 은 이때 조각을 만들지 않고 완성된 응답 하나만 내므로 이벤트도 하나다.
  LlmFlow 가 partial 을 걸러 내는 것이 아니라 모델이 처음부터 조각을 내지 않는 것이다.
  같은 모델이라도 for 루프에 나오는 이벤트 수가 달라진다.
- 도구를 부르는 메시지를 보내면 function_call 과 function_response 는 SSE 모드에서도 partial 없이 온다.
  LiteLlm 이 도구 호출 조각은 모아 두었다가 완성된 것 하나만 내기 때문이다.
  조각으로 오는 것은 텍스트뿐이다.
- 스크립트는 partial 이벤트의 텍스트를 줄바꿈 없이 이어 찍고, 최종 이벤트는 한 줄로 요약한다.
  개행 없이 찍으면 stdout 버퍼가 비워지지 않아 `flush=True` 로 조각마다 내보낸다.

## adk web 에서 확인할 것

- 스크립트를 실행하면 글자가 조금씩 찍히다가 마지막에 `[stream_tool] text ...` 한 줄이 나온다.
- adk web 은 설정의 Token Streaming 을 켜면 요청에 `streaming: true` 를 실어 보낸다.
  서버는 이 값으로 `RunConfig(streaming_mode=StreamingMode.SSE)` 를 만들어 run_async 를 부른다.
- 세션을 다시 불러오면 최종 이벤트만 있다.
  partial 이벤트는 세션에 저장되지 않기 때문이다.

## 이전 단계와 다른 점

runner_01_minimal 의 run 에 streaming 인자가 생기고 run_async 에 RunConfig 를 넘긴다.
partial 이벤트를 구분해 출력하는 분기가 더해졌다.
