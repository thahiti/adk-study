# event_03_transfer

## 이 단계가 보여주는 것

- LlmAgent 에 `sub_agents` 를 주면 ADK 가 `transfer_to_agent` 도구를 자동으로 붙인다.
  모델은 자식의 description 을 보고 넘길지 정한다.
- 전환도 도구 호출이므로 이벤트 모양은 event_02 와 같다.
  function_call 이벤트 다음에 오는 function_response 이벤트의 `actions.transfer_to_agent` 에 대상 이름이 담긴다.
- Runner 는 이 actions 를 보고 같은 턴 안에서 자식을 이어서 실행한다.
  자식이 만든 이벤트는 author 가 자식 name 이고 invocation_id 는 부모와 같다.
- 도구 호출은 content 로, 부수 효과는 actions 로 전달된다는 구분이 여기서 드러난다.

## adk web 에서 확인할 것

- "안녕 하세요 글자 수 세 줘" 라고 보낸다.
- Events 탭에서 transfer_to_agent function_response 이벤트를 펼쳐 actions.transferToAgent 를 본다.
- 이어지는 이벤트의 author 가 event_counter 로 바뀐다.
- 다음 메시지를 보내면 이제 event_counter 가 먼저 응답한다. 이 동작은 runtime-loop 토픽에서 다룬다.

## 이전 단계와 다른 점

count_chars 도구가 자식 event_counter 로 옮겨 가고 부모는 sub_agents 만 가진다.
