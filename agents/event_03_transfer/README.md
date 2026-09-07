# event_03_transfer

## 이 단계가 보여주는 것

- LlmAgent 에 `sub_agents` 를 주면 ADK 가 `transfer_to_agent` 도구를 자동으로 붙인다.
  자식의 name 과 description 이 부모의 system instruction 에 목록으로 들어가고, 도구의 `agent_name` 인자는 그 name 들만 고를 수 있게 제한된다.
  모델은 이 목록을 보고 넘길지 정한다.
- 전환도 도구 호출이므로 이벤트 모양은 event_02 와 같다.
  도구 함수 `transfer_to_agent` 는 값을 돌려주지 않고 `tool_context.actions.transfer_to_agent` 에 대상 이름을 쓴다.
  그래서 function_response 이벤트의 content 는 `{"result": None}` 이고, 대상 이름은 `actions.transfer_to_agent` 에 담긴다.
- 부모의 LLM flow 가 function_response 이벤트를 내보낸 직후 이 actions 를 보고, 같은 InvocationContext 로 자식의 `run_async` 를 호출한다.
  Runner 가 개입하는 것이 아니라 부모 에이전트 실행 안에서 자식이 이어서 돈다.
  그래서 자식이 만든 이벤트는 author 가 자식 name 이고 invocation_id 는 부모와 같다.
- 자식이 최종 응답을 내면 부모의 LLM 루프도 거기서 멈춘다.
  부모 모델은 한 턴에 한 번만 호출된다.
- 도구 호출은 content 로, 부수 효과는 actions 로 전달된다는 구분이 여기서 드러난다.

## adk web 에서 확인할 것

- "안녕 하세요 글자 수 세 줘" 라고 보낸다.
- Events 탭에서 transfer_to_agent function_response 이벤트를 펼쳐 actions.transferToAgent 를 본다.
- 이어지는 이벤트의 author 가 event_counter 로 바뀐다.
- 다음 메시지를 보내면 이제 event_counter 가 먼저 응답한다.
  Runner 가 턴을 시작할 때 세션의 마지막 에이전트 이벤트를 보고 실행할 에이전트를 고르기 때문이다.
  부모가 LlmAgent 이고 disallow_transfer_to_parent 를 켜지 않았으므로 자식에게도 부모로 돌아가는 transfer_to_agent 도구가 붙는다.
  필요하면 부모에게 되돌릴 수 있다.
  이 동작은 runtime-loop 토픽에서 다룬다.

## 이전 단계와 다른 점

count_chars 도구가 자식 event_counter 로 옮겨 가고 부모는 sub_agents 만 가진다.
