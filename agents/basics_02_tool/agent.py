"""basics_02_tool: 파이썬 함수 하나를 도구로 가진 LlmAgent.

tools 에 넘긴 함수는 ADK 가 요청을 만들 때 FunctionTool 로 감싼다.
함수 이름이 도구 이름, 독스트링 전체가 도구 설명, 타입 힌트가
매개변수 스키마가 되어 모델에 전달된다.
"""

import random

from google.adk.agents import LlmAgent

from adk_study.models import make_model


# 독스트링은 그대로 모델에 보내는 도구 설명이므로 모델이 언제 이 도구를
# 쓸지 판단할 내용만 적는다. 구현 메모는 여기처럼 주석에 둔다.
# ADK 1.36.2 는 Args: 절을 따로 해석하지 않는다. 매개변수 스키마에는
# 타입 힌트에서 얻은 타입만 들어가고, Args: 절은 설명 문자열의 일부로
# 통째로 전달된다.
def roll_die(sides: int) -> int:
    """sides 면 주사위를 한 번 굴려 나온 눈을 돌려준다.

    Args:
        sides: 주사위 면의 수.
    """
    # dict 가 아닌 반환값은 ADK 가 {"result": 값} 으로 감싸서
    # function_response 에 넣는다.
    return random.randint(1, sides)


root_agent = LlmAgent(
    name="dice",
    model=make_model(),
    description="주사위를 굴려 주는 에이전트",
    # 도구가 있어도 모델이 알아서 쓰지는 않는다. 언제 어떤 도구를 쓸지
    # instruction 에 적어 준다.
    instruction="사용자가 주사위를 원하면 roll_die 도구를 쓰고 결과를 "
    "한국어로 알려 준다.",
    # 함수를 그대로 넘긴다. BaseTool 이 아닌 callable 은 ADK 가
    # FunctionTool(func=roll_die) 로 감싼다.
    tools=[roll_die],
)
