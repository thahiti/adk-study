# state_04_sequential

## 이 단계가 보여주는 것

- state 는 에이전트 사이의 통신 수단이기도 하다.
  SequentialAgent 는 sub_agents 를 순서대로 실행하고, 앞 에이전트가 output_key 로 남긴 값을 뒤 에이전트가 instruction 의 `{fruits}` 로 읽는다.
- 같은 턴 안인데 뒤 에이전트가 값을 읽을 수 있는 이유는 Runner 의 처리 순서에 있다.
  Runner 는 이벤트를 하나 받을 때마다 먼저 세션에 저장하고 나서 다음 이벤트를 요청한다.
  SequentialAgent 는 첫 에이전트의 이벤트가 모두 소비된 뒤에야 둘째 에이전트를 시작하므로, 둘째 에이전트가 요청을 만드는 시점에는 fruits 가 이미 세션 state 에 있다.
- 여기서는 `{fruits}` 에 `?` 를 붙이지 않는다.
  앞 단계가 반드시 값을 남기므로 없으면 KeyError 로 드러나는 편이 낫다.
- 두 에이전트의 이벤트는 같은 invocation_id 를 가진다.
  자식 에이전트는 부모의 InvocationContext 를 복사해 쓰므로 사용자 메시지 하나가 시작한 한 턴이다.
- SequentialAgent 자체는 model 이 없어 LLM 을 부르지 않고, 이벤트도 만들지 않는다.
  자식의 이벤트가 그대로 올라온다.
  (예외: 콜백이 내용을 돌려주거나 state 를 바꾸면, 또는 resumability 를 켜면 state_pipeline 이름의 이벤트가 생긴다. 이 단계에서는 둘 다 쓰지 않는다.)
- 둘째 에이전트는 첫째 에이전트의 응답을 대화 이력(contents)으로도 받는다.
  같은 세션의 이벤트이므로 include_contents 기본값에서는 요청에 들어가며, 다른 에이전트가 말한 것이라 `For context: [state_lister] said: ...` 형태의 user 역할 메시지로 바뀐다.
  그래도 output_key 와 `{fruits}` 를 쓰는 이유는 어느 값을 어디에 넘기는지 코드에 드러나기 때문이다.

## adk web 에서 확인할 것

- "여름 과일" 이라고 보낸다.
- 채팅창에 state_lister 의 목록과 state_fruit_counter 의 개수가 차례로 나온다.
- State 탭에 fruits 가 있다. 첫 이벤트의 actions.stateDelta 에서 온 값이다.
- Events 탭에서 두 이벤트의 invocationId 가 같고, state_pipeline 이름의 이벤트는 없다.
- state_fruit_counter 이벤트의 모델 요청(request)을 열면 system instruction 에 목록이 들어 있고, contents 끝에 `For context:` 로 시작하는 user 메시지가 있다.

## 이전 단계와 다른 점

LlmAgent 하나가 LlmAgent 둘을 품은 SequentialAgent 로 바뀌었다.
output_key 는 다음 턴의 자기 자신이 아니라 같은 턴의 다음 에이전트에 값을 넘기는 용도로 쓰인다.
값이 세션 state 에 남는 것은 같다.
