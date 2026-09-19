from app.conversations import InMemoryConversationStore


def test_new_conversation_has_empty_history() -> None:
    store = InMemoryConversationStore()

    assert store.get_messages("new-conversation") == ()


def test_successful_exchange_is_stored_in_order() -> None:
    store = InMemoryConversationStore()

    store.append_exchange(
        "conversation-a",
        user_message="Hello.",
        assistant_message="Hi.",
    )

    messages = store.get_messages("conversation-a")

    assert [(message.role, message.content) for message in messages] == [
        ("user", "Hello."),
        ("assistant", "Hi."),
    ]


def test_conversations_are_isolated() -> None:
    store = InMemoryConversationStore()

    store.append_exchange(
        "conversation-a",
        user_message="The codename is Cerberus.",
        assistant_message="Understood.",
    )

    assert store.get_messages("conversation-b") == ()


def test_message_limit_removes_oldest_complete_exchange() -> None:
    store = InMemoryConversationStore(
        max_messages=4,
        max_characters=1_000,
    )

    for number in range(3):
        store.append_exchange(
            "conversation-a",
            user_message=f"user-{number}",
            assistant_message=f"assistant-{number}",
        )

    messages = store.get_messages("conversation-a")

    assert [message.content for message in messages] == [
        "user-1",
        "assistant-1",
        "user-2",
        "assistant-2",
    ]


def test_character_limit_removes_oldest_complete_exchange() -> None:
    store = InMemoryConversationStore(
        max_messages=10,
        max_characters=12,
    )

    store.append_exchange(
        "conversation-a",
        user_message="aaa",
        assistant_message="bbb",
    )
    store.append_exchange(
        "conversation-a",
        user_message="cccc",
        assistant_message="dddd",
    )

    messages = store.get_messages("conversation-a")

    assert [message.content for message in messages] == [
        "cccc",
        "dddd",
    ]


def test_clear_removes_only_selected_conversation() -> None:
    store = InMemoryConversationStore()

    store.append_exchange(
        "conversation-a",
        user_message="A",
        assistant_message="A reply",
    )
    store.append_exchange(
        "conversation-b",
        user_message="B",
        assistant_message="B reply",
    )

    store.clear("conversation-a")

    assert store.get_messages("conversation-a") == ()
    assert len(store.get_messages("conversation-b")) == 2
