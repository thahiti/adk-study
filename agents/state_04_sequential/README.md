# state_04_sequential

## 이 단계가 보여주는 것

- state 는 에이전트 사이의 통신 수단이기도 하다.
  SequentialAgent 는 sub_agents 를 순서대로 실행하고, 앞 에이전트가 output_key 로 남긴 값을 뒤 에이전트가 instruction 의 `{fruits}` 로 읽는다.
- 여기서는 `{fruits}` 에 `?` 를 붙이지 않는다.
  앞 단계가 반드시 값을 남기므로 없으면 KeyError 로 드러나는 편이 낫다.
- 두 에이전트의 이벤트는 같은 invocation_id 를 가진다. 사용자 메시지 하나가 시작한 한 턴이다.
- SequentialAgent 자체는 LLM 을 부르지 않고 이벤트도 만들지 않는다. 자식의 이벤트가 그대로 올라온다.

## adk web 에서 확인할 것

- "여름 과일" 이라고 보낸다.
- 채팅창에 state_lister 의 목록과 state_fruit_counter 의 개수가 차례로 나온다.
- State 탭에 fruits 가 있다. 첫 이벤트의 actions.stateDelta 에서 온 값이다.

## 이전 단계와 다른 점

LlmAgent 하나가 LlmAgent 둘을 품은 SequentialAgent 로 바뀌었다. output_key 는 저장이 아니라 다음 에이전트에 넘기는 용도로 쓰인다.
