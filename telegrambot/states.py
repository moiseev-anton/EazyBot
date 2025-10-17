from aiogram.fsm.state import State, StatesGroup


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

class NavigationStates(StatesGroup):
    level_1 = State()
    level_2 = State()
    level_3 = State()
    level_4 = State()
    level_5 = State()
    final = State()
