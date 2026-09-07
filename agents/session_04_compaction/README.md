# session_04_compaction

## 이 단계가 보여주는 것

- App 은 root_agent 에 앱 수준 설정(플러그인, 이력 압축 등)을 묶는 단위다.
  adk web 은 패키지(`__init__.py`)와 agent.py 에서 App 인스턴스인 `app` 을 `root_agent` 보다 먼저 찾는다.
  이 프로젝트의 `__init__.py` 는 `from . import agent` 뿐이라 agent.py 의 `app` 이 선택된다.
- App 의 name 은 폴더명과 같아야 한다.
  adk web 은 폴더명으로 세션을 만들고 Runner 는 app.name 으로 세션을 찾기 때문이다.
- `events_compaction_config` 를 주면 Runner 가 턴이 끝날 때마다 압축 여부를 검사한다.
  아직 요약에 들어가지 않은 턴이 compaction_interval 개가 되면 그 턴들을 요약한다.
  overlap_size 는 앞 요약 범위의 끝에서 몇 턴을 겹쳐 다시 넣을지다. 0 이면 요약 범위가 겹치지 않는다.
- 요약 요청은 root_agent 의 모델로 나간다.
  LlmAgent 의 흐름을 거치지 않고 모델을 직접 부르므로 요청과 응답은 이벤트로 남지 않는다.
  결과만 `actions.compaction` 이 채워진 이벤트로 세션에 저장된다.
  이 이벤트는 author 가 user 이고 content 가 없으며 요약문은 `actions.compaction.compacted_content` 에 있다.
- 요약기(LlmEventSummarizer)는 첫 압축 시점에 root_agent 의 모델로 한 번 만들어져 config 의 summarizer 에 캐시된다.
  그 뒤 root_agent 의 모델을 바꿔도 요약기는 처음 모델을 계속 쓴다.
- 이후 턴의 모델 요청에서는 요약 범위(타임스탬프 구간)에 든 원본 이벤트가 빠지고 그 자리에 요약이 들어간다.
  요약은 author 가 model 인 이벤트로 취급되어 다른 에이전트의 말처럼 "For context:" 와 "[model] said: ..." 두 파트를 가진 user 콘텐츠로 바뀐다.
  이 변환은 요청을 만들 때마다 일어나고 세션에는 원본 이벤트가 그대로 남는다.
- session_03 이 이력을 아예 끊는다면 이 단계는 이력을 줄여서 보낸다.
- 1.36.2 에서 EventsCompactionConfig 는 실험 기능이라 인스턴스를 만들 때 UserWarning 이 난다.
  agent.py 가 모듈 수준에서 만들므로 import 하는 순간 보인다.

## adk web 에서 확인할 것

- 짧은 대화를 세 턴 주고받는다.
- Events 탭에 둘째 턴 뒤 author 가 user 이고 content 가 없는 이벤트가 생긴다.
  열면 actions.compaction 에 요약문과 요약 범위의 타임스탬프가 있다.
- 셋째 턴 응답 이벤트의 request 를 열면 contents 첫 항목이 "For context:" 와 "[model] said: ..." 이고 첫째, 둘째 턴의 원본 메시지는 없다.
- 셋째 턴 뒤에는 압축이 일어나지 않는다.
  요약에 안 들어간 턴이 하나뿐이라 compaction_interval 에 못 미친다. 넷째 턴 뒤에 다시 일어난다.

## 이전 단계와 다른 점

session_01_inmemory 의 root_agent 는 그대로 두고 App 으로 감싸 events_compaction_config 를 준다.
