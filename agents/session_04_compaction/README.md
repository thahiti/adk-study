# session_04_compaction

## 이 단계가 보여주는 것

- App 은 root_agent 를 감싸 앱 수준 설정을 붙이는 단위다. adk web 은 agent.py 에 `app` 이 있으면 root_agent 보다 먼저 쓴다.
- `events_compaction_config` 를 주면 Runner 가 compaction_interval 턴마다 이력을 요약한다.
  요약 요청은 root_agent 의 모델로 나가고, 결과는 `actions.compaction` 이 채워진 이벤트로 세션에 저장된다.
- 요약기는 첫 압축 시점의 모델로 한 번 만들어져 config 에 캐시된다.
- 이후 턴의 모델 요청은 원본 이벤트 대신 "For context:" 로 시작하는 요약 콘텐츠를 받는다.
  세션에는 원본 이벤트가 그대로 남는다.
- session_03 이 이력을 아예 끊는다면 이 단계는 이력을 줄여서 보낸다.
- 1.36.2 에서 EventsCompactionConfig 는 실험 기능이라 import 시 경고가 난다.

## adk web 에서 확인할 것

- 짧은 대화를 세 턴 주고받는다.
- Events 탭에 author 가 user 이고 actions.compaction 이 있는 이벤트가 둘째 턴 뒤에 생긴다.
- 셋째 턴 응답 이벤트의 request 를 열면 contents 첫 항목이 "For context:" 로 시작한다.

## 이전 단계와 다른 점

session_01_inmemory 의 root_agent 를 App 으로 감싸고 events_compaction_config 를 준다.
