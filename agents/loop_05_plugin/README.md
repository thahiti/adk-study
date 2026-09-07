# loop_05_plugin

## 이 단계가 보여주는 것

- 플러그인은 에이전트가 아니라 러너에 붙는 콜백 묶음이다.
  `BasePlugin` 을 상속해 필요한 콜백만 구현하고 `App(plugins=[...])` 이나 `Runner(plugins=[...])` 로 넣는다.
- 한 턴에서 러너가 부르는 순서는 before_run, before_agent, on_event(이벤트마다), after_agent, after_run 이다.
  자식 에이전트가 돌면 before_agent 와 after_agent 가 자식에 대해서도 불린다.
- on_event 는 러너가 이벤트를 세션에 저장하기 전에 불린다.
  None 을 돌려주면 그대로 두고, Event 를 돌려주면 그것으로 바꾼다. 이 단계는 보기만 한다.
- 콜백은 모두 키워드 전용 인자를 받는다. 시그니처가 다르면 조용히 안 불리는 것이 아니라 TypeError 가 난다.
- agent.py 에 `app` 을 두면 adk web 도 같은 플러그인을 쓰므로, 러너 루프의 각 단계를 터미널 로그로 볼 수 있다.

## adk web 에서 확인할 것

- adk web 을 켠 터미널을 보면서 메시지를 보낸다. `plugin: before_run loop_router` 부터 `plugin: after_run` 까지 찍힌다.
- 둘째 메시지에서는 before_agent 가 loop_specialist 만 나온다. 앞 단계에서 본 다음 턴 선택이 플러그인 로그로도 확인된다.
- 스크립트는 같은 로그를 turn 줄과 함께 찍는다.

## 이전 단계와 다른 점

loop_04_transfer_next_turn 에 LoopTracer 플러그인과 App 이 더해지고, main.py 가 Runner(app=app) 으로 러너를 만든다.
