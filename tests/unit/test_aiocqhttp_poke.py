from unittest.mock import AsyncMock

import pytest

import astrbot.core.message.components as Comp
from astrbot.core.message.message_event_result import MessageChain
from astrbot.core.pipeline.respond.stage import RespondStage
from astrbot.core.platform.astrbot_message import AstrBotMessage, MessageMember
from astrbot.core.platform.message_type import MessageType
from astrbot.core.platform.platform_metadata import PlatformMetadata
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)


def test_poke_to_dict_matches_onebot_v11_segment_format():
    poke = Comp.Poke(type="126", id=2003)
    assert poke.toDict() == {
        "type": "poke",
        "data": {"type": "126", "id": "2003"},
    }


@pytest.mark.asyncio
async def test_respond_stage_treats_poke_with_target_as_non_empty():
    stage = RespondStage()
    chain = [Comp.Poke(type="126", id=2003)]
    assert await stage._is_empty_message_chain(chain) is False


@pytest.mark.asyncio
async def test_aiocqhttp_parse_json_outputs_standard_poke_data():
    chain = MessageChain([Comp.Poke(type="126", id=2003)])
    data = await AiocqhttpMessageEvent._parse_onebot_json(chain)
    assert data == [{"type": "poke", "data": {"type": "126", "id": "2003"}}]


@pytest.mark.asyncio
async def test_aiocqhttp_send_message_dispatches_onebot_v11_poke_payload():
    bot = AsyncMock()
    chain = MessageChain([Comp.Poke(type="126", id=2003)])

    await AiocqhttpMessageEvent.send_message(
        bot=bot,
        message_chain=chain,
        event=None,
        is_group=True,
        session_id="123456",
    )

    bot.send_group_msg.assert_awaited_once_with(
        group_id=123456,
        message=[{"type": "poke", "data": {"type": "126", "id": "2003"}}],
    )


def _make_aiocqhttp_event(message_type: MessageType) -> AiocqhttpMessageEvent:
    message = AstrBotMessage()
    message.type = message_type
    message.self_id = "bot123"
    message.session_id = "123456"
    message.message_id = "msg123"
    message.sender = MessageMember(user_id="123456", nickname="TestUser")
    message.message = [Comp.Plain(text="Hello world")]
    message.message_str = "Hello world"
    if message_type == MessageType.GROUP_MESSAGE:
        message.group_id = "654321"
    message.raw_message = None

    return AiocqhttpMessageEvent(
        message_str="Hello world",
        message_obj=message,
        platform_meta=PlatformMetadata(
            name="aiocqhttp",
            description="Test platform",
            id="test_aiocqhttp",
        ),
        session_id=message.session_id,
        bot=AsyncMock(),
    )


@pytest.mark.asyncio
async def test_aiocqhttp_private_send_typing_calls_set_input_status():
    event = _make_aiocqhttp_event(MessageType.FRIEND_MESSAGE)

    await event.send_typing()

    event.bot.call_action.assert_awaited_once_with(
        "set_input_status",
        user_id=123456,
        event_type=1,
    )


@pytest.mark.asyncio
async def test_aiocqhttp_group_send_typing_is_skipped():
    event = _make_aiocqhttp_event(MessageType.GROUP_MESSAGE)

    await event.send_typing()

    event.bot.call_action.assert_not_awaited()


@pytest.mark.asyncio
async def test_aiocqhttp_stop_typing_is_noop():
    event = _make_aiocqhttp_event(MessageType.FRIEND_MESSAGE)

    await event.stop_typing()

    event.bot.call_action.assert_not_awaited()
