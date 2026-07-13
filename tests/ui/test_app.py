import os

from streamlit.testing.v1 import AppTest


def test_app_title_and_structure() -> None:
    """Test that the app loads without exceptions and basic structure is sound."""
    app_path = os.path.join(os.path.dirname(__file__), "../..", "src", "ui", "app.py")
    at = AppTest.from_file(app_path)
    at.run()

    assert not at.exception


def test_chat_input() -> None:
    """Test that the chat input exists and accepts values."""
    app_path = os.path.join(os.path.dirname(__file__), "../..", "src", "ui", "app.py")
    at = AppTest.from_file(app_path)
    at.run()

    assert not at.exception

    assert len(at.chat_input) > 0

    at.chat_input[0].set_value("Hello!")
    assert at.chat_input[0].value == "Hello!"
