# streaming_02_compare

## 이 단계가 보여주는 것

- 스트리밍은 에이전트 설정이 아니라 한 턴의 RunConfig 로 켠다.
  `RunConfig(streaming_mode=StreamingMode.SSE)` 를 run_async 에 넘긴다.
- SSE 모드에서는 모델이 텍스트를 만드는 동안 조각마다 `partial=True` 이벤트가 온다.
  마지막에 조각을 모두 합친 텍스트가 `partial=False` 이벤트로 온다.
- partial 이벤트는 `is_final_response()` 가 False 이고 Runner 가 세션에 저장하지 않는다.
  세션에는 최종 이벤트 하나만 남으므로 다음 턴의 모델 입력은 스트리밍 여부와 무관하다.
- 기본값 `StreamingMode.NONE` 에서는 LlmFlow 가 partial 응답을 걸러 최종 이벤트만 yield 한다.
  같은 모델이라도 for 루프에 나오는 이벤트 수가 달라진다.
- 스크립트는 partial 이벤트의 텍스트를 줄바꿈 없이 이어 찍고, 최종 이벤트는 한 줄로 요약한다.

## adk web 에서 확인할 것

- 스크립트를 실행하면 글자가 조금씩 찍히다가 마지막에 `[stream_tool] text ...` 한 줄이 나온다.
- adk web 은 오른쪽 위 설정에서 토큰 스트리밍을 켜면 요청에 `streaming: true` 를 실어 같은 SSE 모드로 돈다.
  Events 탭에는 최종 이벤트만 남는다. partial 이벤트는 세션에 저장되지 않기 때문이다.

## 이전 단계와 다른 점

runner_01_minimal 의 run 에 streaming 인자가 생기고 run_async 에 RunConfig 를 넘긴다.
partial 이벤트를 구분해 출력하는 분기가 더해졌다.
