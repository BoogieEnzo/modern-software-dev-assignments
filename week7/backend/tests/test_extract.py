import pytest

from backend.app.services.extract import (
    ActionItem,
    Priority,
    extract_action_items,
    extract_action_items_simple,
)


class TestExtractActionItems:
    """Test enhanced action item extraction."""

    def test_strong_patterns_todo_action(self):
        """Test explicit TODO/ACTION keywords."""
        text = """
        This is a note
        - TODO: write tests
        - ACTION: review PR
        - To-Do: fix bug
        - Task: deploy
        Not actionable
        """
        items = extract_action_items(text)
        descriptions = [item.description for item in items]

        assert "write tests" in descriptions
        assert "review PR" in descriptions
        assert "fix bug" in descriptions
        assert "deploy" in descriptions

    def test_strong_patterns_without_prefix(self):
        """Test strong patterns without list markers."""
        text = """
        todo: update docs
        action: send email
        task: review code
        """
        items = extract_action_items(text)
        descriptions = [item.description for item in items]

        assert "update docs" in descriptions
        assert "send email" in descriptions
        assert "review code" in descriptions

    def test_medium_patterns_action_words(self):
        """Test medium priority patterns with action words."""
        text = """
        Remember to call mom
        I need to finish the report
        Must complete the task ASAP
        Should review the PR
        Don't forget to submit
        """
        items = extract_action_items(text)
        descriptions = [item.description for item in items]

        assert any("call mom" in d for d in descriptions)
        assert any("finish the report" in d for d in descriptions)
        assert any("complete the task" in d for d in descriptions)
        assert any("review the PR" in d for d in descriptions)
        assert any("submit" in d for d in descriptions)

    def test_weak_patterns_exclamation(self):
        """Test weak patterns with exclamation marks."""
        text = """
        This is important!
        Ship it!
        Don't miss this!
        """
        items = extract_action_items(text)
        descriptions = [item.description for item in items]

        assert "This is important!" in descriptions
        assert "Ship it!" in descriptions

    def test_priority_detection_high(self):
        """Test high priority detection."""
        text = """
        URGENT: fix production bug
        Important meeting!!
        """
        items = extract_action_items(text)

        high_priority = [item for item in items if item.priority == Priority.HIGH]
        assert len(high_priority) >= 2

        urgent_items = [item for item in items if "urgent" in item.description.lower()]
        assert any(i.priority == Priority.HIGH for i in urgent_items)

    def test_priority_detection_medium(self):
        """Test medium priority detection."""
        text = """
        Should review this later
        Might need to check
        Consider updating docs
        """
        items = extract_action_items(text)

        medium_priority = [item for item in items if item.priority == Priority.MEDIUM]
        assert len(medium_priority) >= 2

    def test_priority_detection_low(self):
        """Test low priority default."""
        text = """
        Ship it!
        Regular task here
        """
        items = extract_action_items(text)

        low_priority = [item for item in items if item.priority == Priority.LOW]
        assert len(low_priority) >= 1

    def test_deduplication(self):
        """Test that duplicate items are removed."""
        text = """
        TODO: write tests
        TODO: write tests
        write tests
        """
        items = extract_action_items(text)

        descriptions = [item.description for item in items]
        write_tests_count = sum(1 for d in descriptions if "write tests" in d)
        assert write_tests_count == 1

    def test_empty_lines_ignored(self):
        """Test that empty lines are ignored."""
        text = """

        TODO: valid task


        """
        items = extract_action_items(text)

        assert len(items) >= 1

    def test_backward_compatibility_simple(self):
        """Test backward compatibility with simple string list return."""
        text = """
        This is a note
        - TODO: write tests
        - ACTION: review PR
        - Ship it!
        Not actionable
        """
        items = extract_action_items_simple(text)

        assert "write tests" in items
        assert "review PR" in items
        assert "Ship it!" in items

    def test_original_behavior_preserved(self):
        """Test that original test case behavior is preserved."""
        text = """
        This is a note
        - TODO: write tests
        - ACTION: review PR
        - Ship it!
        Not actionable
        """.strip()

        items = extract_action_items(text)
        descriptions = [item.description for item in items]

        assert any("write tests" in d for d in descriptions)
        assert any("review PR" in d for d in descriptions)
        assert any("Ship it!" in d for d in descriptions)

    def test_no_matching_patterns(self):
        """Test text with no actionable items."""
        text = """
        This is just a note
        Nothing to do here
        Just reading
        """
        items = extract_action_items(text)

        assert len(items) == 0

    def test_complex_text(self):
        """Test with complex mixed content."""
        text = """
        Meeting Notes

        - TODO: follow up with client
        - ACTION: update the slides
        - Remember to send the report
        - URGENT: fix the production issue!
        - Should review code later
        Just some notes
        Ship it!
        """
        items = extract_action_items(text)

        assert len(items) >= 6

        high_priority = [item for item in items if item.priority == Priority.HIGH]
        assert len(high_priority) >= 1
