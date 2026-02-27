import os
import pytest
from unittest.mock import patch, MagicMock

from ..app.services.extract import (
    extract_action_items,
    extract_action_items_llm,
    _parse_llm_json_array,
)


# ---------------------------------------------------------------------------
# Helper: build a fake Ollama chat response
# ---------------------------------------------------------------------------
def _fake_ollama_response(content: str):
    """Create a mock object mimicking ollama.chat() return value."""
    resp = MagicMock()
    resp.message.content = content
    return resp


# ===========================================================================
# Tests for the heuristic extractor (extract_action_items)
# ===========================================================================

class TestExtractActionItems:
    def test_extract_bullets_and_checkboxes(self):
        text = """
        Notes from meeting:
        - [ ] Set up database
        * implement API extract endpoint
        1. Write tests
        Some narrative sentence.
        """.strip()

        items = extract_action_items(text)
        assert "Set up database" in items
        assert "implement API extract endpoint" in items
        assert "Write tests" in items

    def test_keyword_prefixed_lines(self):
        text = "todo: Buy groceries\naction: Call dentist\nnext: Review PR"
        items = extract_action_items(text)
        assert len(items) == 3
        assert any("Buy groceries" in i for i in items)
        assert any("Call dentist" in i for i in items)
        assert any("Review PR" in i for i in items)

    def test_empty_input(self):
        assert extract_action_items("") == []
        assert extract_action_items("   ") == []

    def test_deduplication(self):
        text = "- Set up database\n- Set up database\n- set up database"
        items = extract_action_items(text)
        assert len(items) == 1


# ===========================================================================
# Tests for _parse_llm_json_array
# ===========================================================================

class TestParseLlmJsonArray:
    def test_clean_json_array(self):
        raw = '["Buy milk", "Call John"]'
        assert _parse_llm_json_array(raw) == ["Buy milk", "Call John"]

    def test_json_with_surrounding_text(self):
        raw = 'Here are the items:\n["Task A", "Task B"]\nDone.'
        assert _parse_llm_json_array(raw) == ["Task A", "Task B"]

    def test_empty_json_array(self):
        assert _parse_llm_json_array("[]") == []

    def test_filters_empty_strings(self):
        raw = '["Valid item", "", "  ", "Another item"]'
        result = _parse_llm_json_array(raw)
        assert result == ["Valid item", "Another item"]

    def test_invalid_json_raises(self):
        with pytest.raises(Exception):
            _parse_llm_json_array("not json at all")

    def test_non_array_raises(self):
        with pytest.raises(ValueError):
            _parse_llm_json_array('{"key": "value"}')


# ===========================================================================
# Tests for the LLM extractor (extract_action_items_llm)
# ===========================================================================

class TestExtractActionItemsLlm:
    """All tests mock ollama.chat so no running model is required."""

    @patch("week2.app.services.extract.chat")
    def test_bullet_list_input(self, mock_chat):
        mock_chat.return_value = _fake_ollama_response(
            '["Set up database", "Write unit tests", "Deploy to staging"]'
        )
        text = "- Set up database\n- Write unit tests\n- Deploy to staging"
        items = extract_action_items_llm(text)

        assert len(items) == 3
        assert "Set up database" in items
        assert "Write unit tests" in items
        assert "Deploy to staging" in items
        mock_chat.assert_called_once()

    @patch("week2.app.services.extract.chat")
    def test_keyword_prefixed_input(self, mock_chat):
        mock_chat.return_value = _fake_ollama_response(
            '["Buy groceries", "Schedule meeting"]'
        )
        text = "todo: Buy groceries\naction: Schedule meeting"
        items = extract_action_items_llm(text)

        assert len(items) == 2
        assert "Buy groceries" in items
        assert "Schedule meeting" in items

    @patch("week2.app.services.extract.chat")
    def test_empty_input_returns_empty(self, mock_chat):
        items = extract_action_items_llm("")
        assert items == []
        mock_chat.assert_not_called()

    @patch("week2.app.services.extract.chat")
    def test_whitespace_only_returns_empty(self, mock_chat):
        items = extract_action_items_llm("   \n  \t  ")
        assert items == []
        mock_chat.assert_not_called()

    @patch("week2.app.services.extract.chat")
    def test_no_action_items_found(self, mock_chat):
        mock_chat.return_value = _fake_ollama_response("[]")
        items = extract_action_items_llm("The weather is nice today.")
        assert items == []

    @patch("week2.app.services.extract.chat")
    def test_deduplication(self, mock_chat):
        mock_chat.return_value = _fake_ollama_response(
            '["Buy milk", "Buy Milk", "buy milk"]'
        )
        text = "Buy milk, buy milk again"
        items = extract_action_items_llm(text)
        assert len(items) == 1

    @patch("week2.app.services.extract.chat")
    def test_llm_returns_extra_text_around_json(self, mock_chat):
        mock_chat.return_value = _fake_ollama_response(
            'Sure! Here are the action items:\n["Task A", "Task B"]\nHope that helps!'
        )
        items = extract_action_items_llm("Some meeting notes here")
        assert items == ["Task A", "Task B"]

    @patch("week2.app.services.extract.chat")
    def test_fallback_on_invalid_llm_output(self, mock_chat):
        """When LLM returns unparseable output, should fall back to heuristic extractor."""
        mock_chat.return_value = _fake_ollama_response(
            "I could not understand the input, sorry!"
        )
        text = "- Set up database\n- Write tests"
        items = extract_action_items_llm(text)
        assert len(items) >= 1
        assert any("Set up database" in i for i in items)

    @patch("week2.app.services.extract.chat")
    def test_numbered_list_input(self, mock_chat):
        mock_chat.return_value = _fake_ollama_response(
            '["Review PR #42", "Update dependencies", "Fix login bug"]'
        )
        text = "1. Review PR #42\n2. Update dependencies\n3. Fix login bug"
        items = extract_action_items_llm(text)
        assert len(items) == 3

    @patch("week2.app.services.extract.chat")
    def test_mixed_format_input(self, mock_chat):
        mock_chat.return_value = _fake_ollama_response(
            '["Set up database", "Call dentist", "Write docs"]'
        )
        text = (
            "Meeting notes:\n"
            "- [ ] Set up database\n"
            "todo: Call dentist\n"
            "Write docs before Friday."
        )
        items = extract_action_items_llm(text)
        assert len(items) == 3

    @patch("week2.app.services.extract.chat")
    def test_model_name_from_env(self, mock_chat):
        mock_chat.return_value = _fake_ollama_response('["Task"]')
        with patch.dict(os.environ, {"OLLAMA_ACTION_MODEL": "test-model:latest"}):
            extract_action_items_llm("Do something")
        call_kwargs = mock_chat.call_args
        assert call_kwargs.kwargs.get("model") == "test-model:latest" or \
               call_kwargs[1].get("model") == "test-model:latest"
