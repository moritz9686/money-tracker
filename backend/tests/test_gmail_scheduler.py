import inspect

from app.main import _gmail_background_loop


def test_gmail_background_loop_is_a_coroutine() -> None:
    """The scheduler must be suitable for asyncio.create_task."""
    assert inspect.iscoroutinefunction(_gmail_background_loop)
