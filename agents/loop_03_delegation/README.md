# loop_03_delegation

## 이 단계가 보여주는 것

- 커스텀 에이전트는 자식을 직접 돌릴 수 있다.
  `self.sub_agents[0].run_async(ctx)` 가 자식의 이벤트 제너레이터를 돌려주고, 그 이벤트를 다시 yield 해야 러너까지 올라간다.
- 자식은 부모의 InvocationContext 를 복사해 agent 만 자기로 바꿔 쓴다.
  그래서 invocation_id 와 세션이 같고, 자식 이벤트의 author 는 자식 name 이다.
- 자식 이벤트도 러너를 한 번씩 거친다.
  자식이 yield 하면 부모가 다시 yield 하고, 러너가 저장한 뒤에야 부모의 다음 줄이 돈다.
  스크립트에서 `runner: got 자식이 답함` 이 `agent: after child` 보다 먼저 찍히는 것이 그 증거다.
- `sub_agents` 에 넣으면 `child.parent_agent` 가 자동으로 설정된다.
  SequentialAgent 와 ParallelAgent 가 안에서 하는 일이 이것이다.

## adk web 에서 확인할 것

- 메시지를 보내면 "시작", 자식 답, "끝" 세 이벤트가 차례로 나온다.
- Events 탭에서 세 이벤트의 author 가 loop_orchestrator, loop_child, loop_orchestrator 이고 invocationId 가 같다.

## 이전 단계와 다른 점

Announcer 가 자식 LlmAgent 를 품은 Orchestrator 로 바뀌었다. state_delta 는 이 단계의 관심사가 아니라 뺐다.
