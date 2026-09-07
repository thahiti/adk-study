# loop_03_delegation

## 이 단계가 보여주는 것

- 커스텀 에이전트는 자식을 직접 돌릴 수 있다.
  `self.sub_agents[0].run_async(ctx)` 가 자식의 이벤트 제너레이터를 돌려주고, 그 이벤트를 다시 yield 해야 러너까지 올라간다.
- 자식은 부모의 InvocationContext 를 복사해 agent 만 자기로 바꿔 쓴다.
  `BaseAgent.run_async` 가 맨 처음 부르는 `_create_invocation_context` 가 `parent_context.model_copy(update={'agent': self})` 한 줄이다.
  얕은 복사라 invocation_id, session, branch 는 부모 것을 그대로 물려받고, 달라지는 것은 agent 뿐이다.
  그래서 자식 이벤트의 author 는 자식 name 이지만 invocation_id 와 세션은 부모와 같다.
- `run_async` 는 `@final` 이라 부모도 자식도 같은 진입점을 쓴다.
  자식의 before/after agent 콜백은 자식의 `run_async` 안에서 돌고, 부모의 콜백과는 별개다.
- 자식 이벤트도 러너를 한 번씩 거친다.
  자식이 yield 하면 부모가 다시 yield 하고, 러너가 저장한 뒤에야 부모의 다음 줄이 돈다.
  스크립트에서 `runner: got 자식이 답함` 이 `agent: after child` 보다 먼저 찍히는 것이 그 증거다.
- `sub_agents` 에 넣으면 `child.parent_agent` 가 자동으로 설정된다.
  붙는 시점은 부모를 만드는 순간이다. `BaseAgent.model_post_init` 이 `sub_agents` 를 훑어 자기를 부모로 박는다.
  이미 만든 부모의 `sub_agents` 리스트에 나중에 append 하면 붙지 않고, 한 자식을 두 부모에 넣으면 ValueError 가 난다.
- SequentialAgent 도 여기 Orchestrator 와 같은 방식이다.
  자식마다 `sub_agent.run_async(ctx)` 를 돌려 나오는 이벤트를 그대로 다시 yield 한다.
  ParallelAgent 는 다르다. 자식마다 ctx 를 한 번 더 복사해 `<부모>.<자식>` 을 붙인 branch 를 주고, 자식들을 동시에 돌려 이벤트를 합친다.

## adk web 에서 확인할 것

- 메시지를 보내면 "시작", 자식 답, "끝" 세 이벤트가 차례로 나온다.
- Events 탭에서 세 이벤트의 author 가 loop_orchestrator, loop_child, loop_orchestrator 이고 invocationId 가 같다.

## 이전 단계와 다른 점

Announcer 가 자식 LlmAgent 를 품은 Orchestrator 로 바뀌었다. state_delta 는 이 단계의 관심사가 아니라 뺐다.
