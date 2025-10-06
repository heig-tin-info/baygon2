"""Tests for the hierarchical test identifier helpers."""

from __future__ import annotations

import pytest

from baygon.ids import TestId, TrackId


class TestTestId:
    def test_default_root_value(self) -> None:
        assert str(TestId()) == "1"
        assert tuple(TestId()) == (1,)

    def test_construction_from_different_types(self) -> None:
        assert TestId((1, 2, 3)).parts == (1, 2, 3)
        assert TestId("2.5").parts == (2, 5)
        assert TestId(7).parts == (7,)
        assert TestId(TestId("3.4")).parts == (3, 4)

    def test_navigation_helpers(self) -> None:
        root = TestId()
        child = root.down()
        assert str(child) == "1.1"
        assert str(child.next()) == "1.2"
        assert str(child.down(3)) == "1.1.3"
        assert str(child.down(3).next(2)) == "1.1.5"
        assert str(child.up()) == "1"

    def test_pad(self) -> None:
        assert TestId().pad() == ""
        assert TestId("1.2").pad("-") == "-"
        assert TestId("1.2.3").pad("-") == "--"

    def test_invalid_inputs(self) -> None:
        with pytest.raises(ValueError):
            TestId(0)
        with pytest.raises(ValueError):
            TestId("1.0")
        with pytest.raises(ValueError):
            TestId([])
        with pytest.raises(TypeError):
            TestId(object())
        with pytest.raises(ValueError):
            TestId().next(0)
        with pytest.raises(ValueError):
            TestId().down(0)


class TestTrackId:
    def test_next_assigns_identifier(self) -> None:
        tracker = TrackId()
        payload = tracker.next()({"name": "test"})
        assert payload["test_id"] == [1]
        payload = tracker.next()({"name": "test-2"})
        assert payload["test_id"] == [2]

    def test_nested_groups(self) -> None:
        tracker = TrackId()
        tracker.next()({})  # consume "1"
        tracker.down()()
        payload = tracker.next()({})
        assert payload["test_id"] == [1, 1]
        tracker.up()()
        payload = tracker.next()({})
        assert payload["test_id"] == [2]

    def test_reset(self) -> None:
        tracker = TrackId("3.4")
        assert tracker.current.parts == (3, 4)
        tracker.reset()()
        assert tracker.current.parts == (1,)
        tracker.reset("2.7")()
        assert tracker.current.parts == (2, 7)

