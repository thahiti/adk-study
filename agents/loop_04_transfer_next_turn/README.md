# loop_04_transfer_next_turn

## 이 단계가 보여주는 것

- 러너는 턴마다 root_agent 부터 시작하지 않는다.
  새 사용자 메시지를 세션에 붙인 다음 `Runner._find_agent_to_run` 이 세션 이벤트를 뒤에서부터 훑어 이번 턴을 맡을 에이전트를 고른다.
- 훑을 때 author 가 `user` 인 이벤트와 `actions.agent_state` 또는 `actions.end_of_agent` 를 실은 이벤트는 건너뛴다.
  방금 붙인 사용자 메시지가 늘 마지막 이벤트이므로 이 건너뛰기가 없으면 아무것도 고를 수 없다.
- 처음 만난 에이전트 이벤트의 author 를 이렇게 해석한다.
  root_agent 의 name 이면 root_agent 다.
  트리에 없는 이름이면 경고 로그를 남기고 더 앞의 이벤트를 계속 본다.
  트리에서 찾았으면 `_is_transferable_across_agent_tree` 로 그 에이전트가 자기부터 root 까지 부모로 되돌아갈 수 있는지 확인하고, 그럴 때만 고른다.
  아니면 더 앞의 이벤트를 보고, 끝까지 못 찾으면 root_agent 로 되돌아간다.
- 규칙 앞에 예외가 하나 있다.
  세션의 마지막 이벤트가 함수 응답이면 위 훑기를 건너뛰고 짝이 되는 함수 호출을 냈던 에이전트를 고른다.
  이때는 전환 가능 여부를 보지 않는다.
- 첫 턴에서 부모가 `transfer_to_agent` 로 넘기면 마지막 에이전트 이벤트의 author 가 자식이고 자식은 전환 가능하므로, 둘째 턴은 부모 모델을 한 번도 부르지 않고 자식이 바로 받는다.
  이 선택은 에이전트 코드가 아니라 러너가 한다. 세션 이력이 곧 다음 턴의 시작점이다.
- 자식에게 붙는 전환 대상은 자기 sub_agents 와, 부모가 LlmAgent 일 때의 부모와 형제들이다.
  여기서는 대상이 부모 하나뿐이라 자식은 필요하면 loop_router 로 되돌릴 수 있다.
- `disallow_transfer_to_parent=True` 는 두 곳을 한꺼번에 막는다.
  대상 목록에서 부모가 빠지고 남는 대상이 없으면 transfer_to_agent 도구 자체가 붙지 않는다.
  동시에 `_is_transferable_across_agent_tree` 가 False 가 되어 둘째 턴을 자식이 이어받지 못하고 러너가 root_agent 를 고른다.

## adk web 에서 확인할 것

- 첫 메시지를 보내면 Events 탭에 loop_router 의 transfer 와 loop_specialist 의 답이 있다.
- 둘째 메시지를 보내면 loop_specialist 의 답만 생기고 loop_router 이벤트는 없다.
- 스크립트는 `turn 1: loop_router, loop_router, loop_specialist` 와 `turn 2: loop_specialist` 를 찍는다.

## 이전 단계와 다른 점

커스텀 Orchestrator 가 LlmAgent 부모와 자식으로 바뀌고, main.py 가 한 세션에 두 턴을 보낸다.
