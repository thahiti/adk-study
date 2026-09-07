"""loop_01_pause_resume: yield 가 러너로 제어를 넘기고 다시 받는 지점.

출력 순서 자체가 이 단계의 학습 내용이라 print 를 잡아서 검증한다.
모델을 부르지 않으므로 FakeLlm 도 필요 없다.
"""

from google.adk.runners import InMemoryRunner
from google.genai import types

from agents.loop_01_pause_resume.agent import root_agent
from agents.loop_01_pause_resume.main import run, text_of


async def test_agent_and_runner_lines_interleave(capsys):
    """에이전트 줄과 러너 줄이 번갈아 나오는지 본다.

    에이전트가 이벤트를 다 만든 뒤 러너가 받는 구조라면 agent 네 줄이
    먼저 몰려 나왔을 것이다. 실제로는 yield 마다 멈추므로 섞여 나온다.
    """
    await run(root_agent, "시작")

    # capsys 는 pytest 가 가로챈 표준 출력을 돌려준다
    lines = capsys.readouterr().out.strip().splitlines()
    assert lines == [
        "agent: before yield 1",
        "runner: got 첫 번째 알림",
        "agent: after yield 1",
        "agent: before yield 2",
        "runner: got 두 번째 알림",
        # 마지막 yield 뒤의 줄은 호출자가 한 번 더 요청할 때 실행된다.
        # 그 요청이 생성자를 끝내며 async for 루프도 함께 끝난다.
        "agent: after yield 2",
    ]


async def test_run_collects_both_events():
    events = await run(root_agent, "시작")

    assert [e.content.parts[0].text for e in events] == [
        "첫 번째 알림",
        "두 번째 알림",
    ]
    assert events[1].actions.state_delta == {"announced": 2}


async def test_event_is_stored_before_the_caller_receives_it():
    """러너가 저장을 끝낸 뒤에 호출자에게 넘긴다는 것을 확인한다.

    이벤트를 받은 시점에 세션을 다시 읽으면 방금 받은 이벤트가 이미
    마지막에 들어가 있고 state_delta 도 반영이 끝나 있다. 그동안
    에이전트는 yield 에서 멈춰 있으므로, 러너는 다음 이벤트에 밀리지
    않고 이벤트 하나를 온전히 처리할 수 있다.
    """
    runner = InMemoryRunner(agent=root_agent, app_name="test")
    session = await runner.session_service.create_session(
        app_name="test", user_id="user"
    )
    message = types.Content(
        role="user", parts=[types.Part.from_text(text="시작")]
    )

    seen = []
    async for event in runner.run_async(
        user_id="user", session_id=session.id, new_message=message
    ):
        stored = await runner.session_service.get_session(
            app_name="test", user_id="user", session_id=session.id
        )
        assert stored is not None
        # 방금 받은 이벤트가 세션의 마지막 이벤트다
        assert stored.events[-1].id == event.id
        seen.append((text_of(event), stored.state.get("announced")))

    # 첫 이벤트를 받는 시점에는 announced 가 아직 없고, state_delta 를
    # 실은 두 번째 이벤트를 받는 시점에는 이미 반영돼 있다
    assert seen == [("첫 번째 알림", None), ("두 번째 알림", 2)]
