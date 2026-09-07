# session_03_include_contents

## 이 단계가 보여주는 것

- 세션의 events 가 그대로 모델 입력이 되는 것이 기본이다.
  `include_contents="default"` 면 LlmAgent 가 매 요청에 세션 이력을 contents 로 넣는다.
- 허용 값은 `"default"` 와 `"none"` 둘뿐이고 기본값은 `"default"` 다.
- `include_contents="none"` 이면 이번 턴만 보낸다.
  이번 턴은 마지막 사용자 메시지부터 지금까지의 이벤트다.
  앞 턴의 대화는 빠지지만 이번 턴 안에서 일어난 도구 호출과 결과는 그대로 들어간다.
  그래서 도구는 "none" 이어도 정상으로 동작한다.
- 세션에는 여전히 모든 이벤트가 쌓이지만 모델은 앞 턴을 모른다.
  세션 이력(저장)과 모델 컨텍스트(전송)는 다른 개념이다. 이 옵션이 그 둘을 가른다.
- instruction 은 contents 가 아니라 system instruction 으로 가므로 "none" 이어도 매번 전달된다.

## adk web 에서 확인할 것

- "내 이름은 철수야" 를 보내고 "내 이름이 뭐지" 를 보낸다. 모델이 이름을 모른다고 답한다.
- Events 탭에는 네 이벤트가 모두 남아 있다.
- 둘째 응답 이벤트의 request 를 열면 contents 에 마지막 사용자 메시지 하나만 있다.
- "세션 알려 줘" 를 보내면 도구가 events 수를 6 이라고 답한다.
  모델이 앞 턴을 몰라도 세션에는 앞 턴이 남아 있다는 뜻이다.
  이 응답 이벤트의 request 에는 이번 턴의 사용자 메시지, function_call, function_response 가 들어 있다.
- session_01_inmemory 에서 같은 대화를 하면 이름을 기억한다.

## 이전 단계와 다른 점

session_01_inmemory 에 `include_contents="none"` 한 줄이 더해졌다.
