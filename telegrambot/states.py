from aiogram.fsm.state import State, StatesGroup


class FacultyStates(StatesGroup):
    choosing_faculty = State()
    choosing_course = State()
    choosing_group = State()
    choosing_action = State()
    action = State()


class TeacherStates(StatesGroup):
    choosing_letter = State()
    choosing_teacher = State()
    choosing_action = State()
    action = State()


class NavigationStates(StatesGroup):
    level_1 = State()
    level_2 = State()
    level_3 = State()
    level_4 = State()
    level_5 = State()
    final = State()
