# loop_05_plugin

## 이 단계가 보여주는 것

- 플러그인은 에이전트가 아니라 러너에 붙는 콜백 묶음이다.
  에이전트 콜백이 그 에이전트 하나에만 걸리는 것과 달리 플러그인은 러너가 돌리는 모든 에이전트에 걸린다.
- `BasePlugin` 을 상속해 필요한 콜백만 구현하고 `App(plugins=[...])` 으로 넣는다.
  `Runner(plugins=[...])` 도 아직 받지만 1.36.2에서 deprecated 이고 `app` 과 같이 줄 수 없다.
- 한 턴에서 러너가 부르는 순서는 before_run, before_agent, on_event(이벤트마다), after_agent, after_run 이다.
  자식 에이전트가 돌면 before_agent 와 after_agent 가 자식에 대해서도 불리고, 이때 순서는 부모 안에 자식이 들어가는 모양이다.
  첫 턴 로그는 before_run, before_agent(부모), on_event 둘, before_agent(자식), on_event, after_agent(자식), after_agent(부모), after_run 이다.
- before_run 의 `invocation_context.agent` 는 root_agent 가 아니라 러너가 이번 턴에 실행하기로 고른 에이전트다.
  전환이 끝난 다음 턴에서는 `before_run loop_specialist` 가 찍힌다.
- on_event 는 러너가 이벤트를 세션에 저장하기 전에 불린다.
  None 을 돌려주면 그대로 두고, Event 를 돌려주면 그 Event 에서 값을 넣은 필드만 원래 이벤트에 덮어써서 저장하고 흘려보낸다.
  id 와 invocation_id, timestamp 는 바뀌지 않는다. 이 단계는 보기만 한다.
- 어떤 콜백이든 None 이 아닌 값을 돌려주면 뒤에 오는 플러그인과 에이전트 자신의 콜백을 건너뛴다.
  관찰만 하려면 반드시 None 을 돌려줘야 한다.
- 콜백은 모두 키워드 전용 인자를 받는다. 시그니처가 다르면 조용히 안 불리는 것이 아니라 예외가 난다.
  PluginManager 가 콜백의 예외를 잡아 RuntimeError 로 감싸 던지므로 실제로 보이는 것은 TypeError 를 원인으로 가진 RuntimeError 다.
- 여기서 쓰는 다섯 개 말고 before_model, after_model, before_tool, after_tool, on_user_message, on_model_error, on_tool_error 도 같은 방식으로 구현한다.
- agent.py 에 `app` 을 두면 adk web 도 같은 플러그인을 쓰므로, 러너 루프의 각 단계를 터미널 로그로 볼 수 있다.
  adk web 은 agent.py 에서 `app` 을 먼저 찾고 없을 때만 `root_agent` 를 쓴다.

## adk web 에서 확인할 것

- adk web 을 켠 터미널을 보면서 메시지를 보낸다. `plugin: before_run loop_router` 부터 `plugin: after_run` 까지 찍힌다.
- 둘째 메시지에서는 before_agent 가 loop_specialist 만 나온다. 앞 단계에서 본 다음 턴 선택이 플러그인 로그로도 확인된다.
- 스크립트는 같은 로그를 turn 줄과 함께 찍는다. plugin 줄이 먼저 흐르고 턴이 끝난 뒤 turn 줄이 나온다.

## 이전 단계와 다른 점

loop_04_transfer_next_turn 에 LoopTracer 플러그인과 App 이 더해지고, main.py 가 Runner(app=app) 으로 러너를 만든다.
`app` 을 주면 root_agent 와 플러그인을 App 에서 가져오므로 `agent=` 는 같이 줄 수 없다. 같이 주면 ValueError 다.
