import sys
import unittest
from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "telegrambot"))

from api_client import AsyncClientSession, models_as_jsonschema
from api_client.client_patch import patch_jsonapi_client

patch_jsonapi_client(verbose=False)

from callbacks import NotificationCallback
from config import settings
from context import request_context
from dto.notification_preference_dto import NotificationPreferenceDTO
from dto import AuthDTO, UserDTO
from enums import ScheduleStyle
from keyboards import get_settings_keyboard
from services.user_service import UserService
from repositories.account_repository import JsonApiAccountRepository
from repositories.exceptions import ApiError
from repositories.notification_preference_repository import JsonApiNotificationPreferenceRepository
from services.notification_preferences import NotificationPreferences


def resource(id="123", account="45", kind="lesson_upcoming", enabled=True, channel=None):
    return {
        "type": "notification-preferences", "id": id,
        "attributes": {"notificationType": kind, "channel": channel or settings.platform,
                       "enabled": enabled, "updatedAt": "2026-10-21T09:00:00Z"},
        "relationships": {"socialAccount": {"data": {"type": "social-accounts", "id": account}}},
    }


def preference(id="123", account="45", kind="lesson_upcoming", enabled=True, channel=None):
    return NotificationPreferenceDTO(
        id=id, social_account_id=account, notification_type=kind,
        channel=channel or settings.platform, enabled=enabled, updated_at="v1",
    )


class NotificationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.client = AsyncClientSession("https://example.test/api/v1", settings.platform,
                                         "test-secret", schema=models_as_jsonschema)
        self.token = request_context.set({"user_id": "777", "hmac": False})

    async def asyncTearDown(self):
        await self.client._aiohttp_session.close()
        request_context.reset(self.token)

    async def test_pagination_including_empty_page_and_camel_case(self):
        self.client.http_request_async = AsyncMock(side_effect=[
            (200, {"data": [], "links": {"next": {"href": "?page=2"}}}, None),
            (200, {"data": [resource()], "links": {"next": None}}, None),
        ])
        result = await JsonApiNotificationPreferenceRepository(self.client).get_preferences()
        self.assertEqual(result[0].social_account_id, "45")
        self.assertEqual(result[0].notification_type, "lesson_upcoming")
        self.assertIn("?page=2", self.client.http_request_async.call_args.args[1])

    async def test_patch_only_enabled_and_confirm_with_fresh_get(self):
        self.client.http_request_async = AsyncMock(side_effect=[
            (200, {"data": resource(enabled=False)}, None),
            (200, {"data": resource(enabled=False)}, None),
        ])
        result = await JsonApiNotificationPreferenceRepository(self.client).set_enabled("123", False)
        call = self.client.http_request_async.call_args_list[0]
        self.assertEqual(call.args[0], "patch")
        headers = self.client._build_authenticated_request_kwargs(call.args[0], call.args[1])["headers"]
        self.assertEqual(headers["Content-Type"], "application/vnd.api+json")
        self.assertEqual(headers["Accept"], "application/vnd.api+json")
        self.assertEqual(call.kwargs["send_json"], {"data": {
            "type": "notification-preferences", "id": "123", "attributes": {"enabled": False}}})
        self.assertFalse(result.enabled)
        with self.assertRaises(TypeError):
            await JsonApiNotificationPreferenceRepository(self.client).set_enabled("123", 0)

    async def test_find_exact_account_on_second_page(self):
        def account(id, social_id):
            return {"type": "social-accounts", "id": id,
                    "attributes": {"platform": settings.platform, "socialId": social_id,
                                   "chatId": social_id, "extraData": {}}}
        self.client.http_request_async = AsyncMock(side_effect=[
            (200, {"data": [account("44", "888")], "links": {"next": "?page=2"}}, None),
            (200, {"data": [account("45", "777")]}, None),
        ])
        repo = JsonApiAccountRepository(self.client)
        self.assertEqual(await repo.get_current_account_id(settings.platform, "777"), "45")

    async def test_auth_account_id_used_and_checked(self):
        repo = JsonApiAccountRepository(self.client)
        repo.authenticated_accounts[(settings.platform, "777")] = "45"
        self.client.http_request_async = AsyncMock(return_value=(200, {"data": {
            "type": "social-accounts", "id": "45",
            "attributes": {"platform": settings.platform, "socialId": "777",
                           "chatId": "777", "extraData": {}}}}, None))
        self.assertEqual(await repo.get_current_account_id(settings.platform, "777"), "45")
        self.assertTrue(self.client.http_request_async.call_args.args[1].endswith("/social-accounts/45/"))
        with self.assertRaises(ApiError):
            await repo.get_current_account_id(settings.platform, "999")

    async def test_filter_current_account_and_platform(self):
        service = NotificationPreferences()
        accounts = SimpleNamespace(get_current_account_id=AsyncMock(return_value="45"))
        repo = SimpleNamespace(get_preferences=AsyncMock(return_value=[
            preference(account="99"), preference(), preference(kind="schedule_updated", id="124")]))
        result = await service.get_preferences("777", account_repo=accounts, preference_repo=repo)
        self.assertEqual(len(result), 2)
        self.assertTrue(all(p.social_account_id == "45" for p in result.values()))
        repo.get_preferences.return_value = [preference(channel="wrong-platform")]
        with self.assertRaises(ApiError):
            await service.get_preferences("777", account_repo=accounts, preference_repo=repo)
        repo.get_preferences.return_value = []
        with self.assertRaises(ApiError):
            await service.get_preferences("777", account_repo=accounts, preference_repo=repo)

    async def test_stale_and_repeated_clicks_do_not_patch(self):
        @asynccontextmanager
        async def lock(*args, **kwargs):
            yield
        storage = SimpleNamespace(redis=SimpleNamespace(lock=lock))
        current = preference()
        service = NotificationPreferences()
        service.get_preferences = AsyncMock(return_value={"lesson_upcoming": current})
        repo = SimpleNamespace(set_enabled=AsyncMock(return_value=current.model_copy(update={"enabled": False})))
        await service.set_enabled("777", "lesson_upcoming", False, "outdated",
                                  storage=storage, preference_repo=repo)
        repo.set_enabled.assert_not_awaited()
        result = await service.set_enabled("777", "lesson_upcoming", False, current.version,
                                           storage=storage, preference_repo=repo)
        service.get_preferences.return_value = result
        await service.set_enabled("777", "lesson_upcoming", False, current.version,
                                  storage=storage, preference_repo=repo)
        repo.set_enabled.assert_awaited_once_with("123", False)

    async def test_patch_failure_propagates(self):
        @asynccontextmanager
        async def lock(*args, **kwargs):
            yield
        current = preference()
        service = NotificationPreferences()
        service.get_preferences = AsyncMock(return_value={"lesson_upcoming": current})
        repo = SimpleNamespace(set_enabled=AsyncMock(side_effect=ApiError("400")))
        with self.assertRaises(ApiError):
            await service.set_enabled("777", "lesson_upcoming", False, current.version,
                                      storage=SimpleNamespace(redis=SimpleNamespace(lock=lock)),
                                      preference_repo=repo)

    def test_callback_payload_has_no_preference_id_and_fits(self):
        current = preference()
        callback = NotificationCallback(notification_type=current.notification_type,
                                        enabled=False, version=current.version)
        self.assertLessEqual(len(callback.pack().encode()), 64)
        self.assertEqual(NotificationCallback.unpack(callback.pack()).enabled, False)

    def test_both_menu_styles_without_subscription(self):
        user = UserDTO(id="1", first_name="Test", username="test")
        preferences = {kind: preference(kind=kind) for kind in ("schedule_updated", "lesson_upcoming")}
        for style in ScheduleStyle:
            keyboard = get_settings_keyboard(user, preferences, style)
            callbacks = [button.callback_data for row in keyboard.inline_keyboard for button in row
                         if button.callback_data and button.callback_data.startswith("notify:")]
            self.assertEqual(len(callbacks), 2)
            self.assertEqual({NotificationCallback.unpack(value).notification_type for value in callbacks},
                             set(preferences))

    def test_blocked_flag_is_read_without_being_sent_during_auth(self):
        auth = self.client.create(_type="social-accounts", platform=settings.platform,
                                  social_id="777", chat_id="777")
        auth.validate()
        self.assertNotIn("isBlocked", auth._commit_data()["data"]["attributes"])
        with self.assertNoLogs("jsonapi_client.resourceobject", level="WARNING"):
            document = self.client.read({"data": {
                "type": "social-accounts", "id": "45",
                "attributes": {"platform": settings.platform, "socialId": "777",
                               "chatId": "777", "isBlocked": False},
            }}, no_cache=True)
        self.assertIs(document.resource.is_blocked, False)

    async def test_reauthorization_only_authenticates_and_reads_user(self):
        user = UserDTO(id="1", first_name="Test", username="test")
        account = SimpleNamespace(id=45, user=None)
        account_repo = SimpleNamespace(get_or_create=AsyncMock(return_value=account))
        user_repo = SimpleNamespace(get_user=AsyncMock(return_value=user), update_user=AsyncMock())
        result = await UserService().auth_user(
            AuthDTO(social_id="777", chat_id="777", last_name="", nonce="nonce"),
            account_repo=account_repo, user_repo=user_repo,
        )
        self.assertEqual(result.id, 45)
        user_repo.update_user.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
