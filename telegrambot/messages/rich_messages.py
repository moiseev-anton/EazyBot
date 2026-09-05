from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputRichBlockBlockQuotation,
    InputRichBlockButtons,
    InputRichBlockFooter,
    InputRichBlockParagraph,
    InputRichBlockSectionHeading,
    InputRichMessage,
    RichTextBold,
    RichTextItalic,
    RichTextMarked,
    RichMessageButton,
)

from callbacks import SubscriptionCallback
from dto import DateSpanDTO, LessonDTO, UserDTO
from dto.base_dto import SubscriptableDTO
from enums import Branch, NavigationAction, SubscriptionAction

from .formatters import format_rich_schedule


_ENTITY_LABELS = {
    Branch.GROUPS: "Группа",
    Branch.TEACHERS: "Преподаватель",
}

def get_rich_main_message(user: UserDTO) -> InputRichMessage:
    """Форматирует главный экран для нового интерфейса Telegram."""
    blocks = [
        InputRichBlockSectionHeading(text=f"👤 {user.name}", size=2),
        InputRichBlockParagraph(text=f"> {user.username}"),
        InputRichBlockSectionHeading(text="⭐ Ваше расписание", size=3),
    ]
    if user.subscriptions:
        blocks.append(
            InputRichBlockBlockQuotation(
                blocks=[
                    InputRichBlockParagraph(
                        text=RichTextBold(text=user.subscriptions[0].button_name)
                    )
                ]
            )
        )
    else:
        blocks.append(
            InputRichBlockBlockQuotation(
                blocks=[
                    InputRichBlockParagraph(text=RichTextMarked(text="Не выбрано")),
                    InputRichBlockParagraph(
                        text=(
                            "Подпишитесь на расписание, чтобы получать уведомления "
                            "и быстро открывать его с главного экрана."
                        )
                    ),
                ]
            )
        )
    return InputRichMessage(blocks=blocks)


def add_rich_keyboard(
        message: InputRichMessage,
        keyboard: InlineKeyboardMarkup,
) -> InputRichMessage:
    """Добавляет кнопки inline-клавиатуры в rich-сообщение без смены callback-данных."""
    for row in keyboard.inline_keyboard:
        message.blocks.append(
            InputRichBlockButtons(
                buttons=[_to_rich_button(button) for button in row]
            )
        )
    return message


def add_rich_footer(message: InputRichMessage, text: str) -> InputRichMessage:
    message.blocks.append(InputRichBlockFooter(text=RichTextItalic(text=text)))
    return message


def add_rich_note(message: InputRichMessage, text: str) -> InputRichMessage:
    message.blocks.append(InputRichBlockParagraph(text=RichTextItalic(text=text)))
    return message


def _to_rich_button(button: InlineKeyboardButton) -> RichMessageButton:
    style = "primary" if button.text in {"🔄 Обновить", "🔄 Сегодня"} else None
    if button.callback_data:
        return RichMessageButton(
            text=button.text,
            style=style,
            callback_data=button.callback_data,
        )
    if button.url:
        return RichMessageButton(text=button.text, style=style, url=button.url)
    raise ValueError(f"Unsupported inline button type: {button!r}")


def get_rich_choosing_message(
        title: str,
        prompt: str,
        context: str | None = None,
) -> InputRichMessage:
    blocks = [
        InputRichBlockSectionHeading(text=title, size=2),
    ]
    if context:
        blocks.append(
            InputRichBlockBlockQuotation(
                blocks=[InputRichBlockParagraph(text=context)]
            )
        )
    blocks.append(InputRichBlockParagraph(text=prompt))
    return InputRichMessage(blocks=blocks)


def get_rich_selected_message(
        obj: SubscriptableDTO,
        branch: Branch,
    is_subscribed: bool,
) -> InputRichMessage:
    blocks = [
        InputRichBlockParagraph(text=_ENTITY_LABELS[branch]),
        InputRichBlockSectionHeading(text=obj.display_name, size=2),
    ]
    if is_subscribed:
        blocks.append(InputRichBlockParagraph(text="✅ Вы подписаны"))
    return InputRichMessage(blocks=blocks)


def get_rich_subscription_replacement_warning() -> InputRichMessage:
    return InputRichMessage(blocks=[
        InputRichBlockSectionHeading(text="⚠️ Заменить расписание?", size=2),
        InputRichBlockParagraph(
            text="Предыдущая подписка будет отменена."
        ),
        InputRichBlockButtons(
            buttons=[
                RichMessageButton(
                    text="Продолжить",
                    style="success",
                    callback_data=NavigationAction.CONFIRM,
                )
            ]
        ),
    ])


def get_rich_settings_message(user: UserDTO) -> InputRichMessage:
    message = get_rich_main_message(user)
    if user.subscriptions:
        message.blocks.append(
            InputRichBlockSectionHeading(text="Подписки", size=3)
        )
        for subscription in user.subscriptions:
            message.blocks.append(
                InputRichBlockButtons(
                    buttons=[
                        RichMessageButton(
                            text=f"✖️ Отписаться от {subscription.button_name}",
                            style="danger",
                            callback_data=SubscriptionCallback(
                                action=SubscriptionAction.UNSUBSCRIBE,
                                sub_id=subscription.id,
                            ).pack(),
                        )
                    ]
                )
            )
    return message


def get_rich_start_message(text: str) -> InputRichMessage:
    return InputRichMessage(blocks=[InputRichBlockParagraph(text=text)])


def get_rich_schedule_msg(
        target_obj: SubscriptableDTO,
        lessons: list[LessonDTO],
        date_range: DateSpanDTO,
) -> InputRichMessage:
    """Форматирует rich-сообщение с расписанием для группы или преподавателя."""
    return format_rich_schedule(target_obj, lessons, date_range)
