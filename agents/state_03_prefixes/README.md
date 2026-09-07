# state_03_prefixes

## 이 단계가 보여주는 것

- state 키의 접두어가 범위를 정한다.
  - 접두어 없음: 이 세션에만 남는다.
  - `user:`: 같은 app_name 과 user_id 의 모든 세션이 공유한다.
  - `app:`: 같은 app_name 의 모든 사용자가 공유한다.
  - `temp:`: 이 턴 안에서만 읽을 수 있고 저장되지 않는다. 이벤트 delta 에서도 빠진다.
- 새 세션을 만들면 세션 서비스가 user: 와 app: 값을 병합해서 돌려준다.
- 쓰는 코드는 접두어만 다르고 같다. 범위는 세션 서비스가 해석한다.

## adk web 에서 확인할 것

- "올려" 를 두 번 보내고 State 탭을 본다. count, user:total, app:hits 가 모두 2 다. temp:last_call 은 없다.
- 새 세션을 만들고 "올려" 를 보낸다. count 는 1, user:total 과 app:hits 는 3 이다.
- 왼쪽 위 사용자 이름을 바꿔 새 세션을 만들고 "올려" 를 보낸다. app:hits 만 이어서 늘어난다.

## 이전 단계와 다른 점

bump_counter 가 count 외에 user:total, app:hits, temp:last_call 을 함께 쓴다.
