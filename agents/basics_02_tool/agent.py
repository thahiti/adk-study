"""basics_02_tool: 파이썬 함수 하나를 도구로 가진 LlmAgent."""

import random

from google.adk.agents import LlmAgent

from adk_study.models import make_model


def roll_die(sides: int) -> int:
    """sides 면 주사위를 한 번 굴려 나온 눈을 돌려준다.

    Args:
        sides: 주사위 면의 수.
    """
    return random.randint(1, sides)


root_agent = LlmAgent(
    name="dice",
    model=make_model(),
    description="주사위를 굴려 주는 에이전트",
    instruction="사용자가 주사위를 원하면 roll_die 도구를 쓰고 결과를 "
    "한국어로 알려 준다.",
    tools=[roll_die],
)
