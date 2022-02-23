def asserting(condition, msg: str) -> None:
    if not condition:
        raise AssertionError(msg)
