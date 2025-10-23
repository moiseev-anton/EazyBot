from functools import wraps
from typing import Iterable

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from exceptions import StateExpiredError


class GroupStates(StatesGroup):
    choosing_faculty = State()
    choosing_grade = State()
    choosing_group = State()


class TeacherStates(StatesGroup):
    choosing_letter = State()
    choosing_teacher = State()


class ActionStates(StatesGroup):
    choosing_action = State()
    reading_schedule = State()
    waiting_sub_confirm = State()


async def get_state_data(
        state: FSMContext,
        required_keys: Iterable[str] = (),
) -> dict:
    """Извлекает и проверяет контекст FSM."""
    data = await state.get_data()

    if not data:
        raise StateExpiredError("No context data found")

    missing = [k for k in required_keys if k not in data or data[k] is None]
    if missing:
        raise StateExpiredError(f"Missing required context fields: {', '.join(missing)}")

    return data


def require_state_date(*required_keys: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(event, state: FSMContext, *args, **kwargs):
            data = await get_state_data(state, required_keys)
            return await func(event, state, state_data=data, *args, **kwargs)

        return wrapper

    return decorator
