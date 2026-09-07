# loop_05_plugin

## 이 단계가 보여주는 것

- 러너는 턴마다 root_agent 부터 시작하지 않는다.
  `run_async` 는 세션의 이벤트를 뒤에서부터 보고 마지막 에이전트 이벤트의 author 를 찾아 그 에이전트를 실행한다.
- 첫 턴에서 부모가 `transfer_to_agent` 로 자식에게 넘기면 마지막 이벤트의 author 는 자식이다.
  둘째 턴은 부모 모델을 부르지 않고 자식이 바로 받는다.
- 이 선택은 에이전트 코드가 아니라 러너의 `_find_agent_to_run` 이 한다.
  세션 이력이 곧 다음 턴의 시작점이다.
- 자식에게는 부모로 돌아가는 transfer_to_agent 도구가 붙어 있으므로 필요하면 다시 부모에게 넘길 수 있다.
  `disallow_transfer_to_parent=True` 를 주면 그 길을 막는다.

## adk web 에서 확인할 것

- 첫 메시지를 보내면 Events 탭에 loop_router 의 transfer 와 loop_specialist 의 답이 있다.
- 둘째 메시지를 보내면 loop_specialist 의 답만 생기고 loop_router 이벤트는 없다.
- 스크립트는 `turn 1: loop_router, loop_router, loop_specialist` 와 `turn 2: loop_specialist` 를 찍는다.

## 이전 단계와 다른 점

커스텀 Orchestrator 가 LlmAgent 부모와 자식으로 바뀌고, main.py 가 한 세션에 두 턴을 보낸다.
