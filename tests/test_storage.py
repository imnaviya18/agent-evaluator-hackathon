from sandbox.trace_storage import TraceStorage


def test_save_and_load_trace(tmp_path):
    storage = TraceStorage(tmp_path / "data")

    sample_trace = {
        "test_id": "TEST_ABC123",
        "agent_name": "TestAgent",
        "scenario_name": "Sample",
        "success": True,
        "tool_calls": [],
    }

    path = storage.save_trace(sample_trace)

    assert path

    loaded = storage.load_trace("TEST_ABC123")

    assert loaded is not None
    assert loaded["test_id"] == "TEST_ABC123"


def test_available_dates(tmp_path):
    storage = TraceStorage(tmp_path / "data")

    storage.save_trace(
        {
            "test_id": "TEST_DATE_001",
            "agent_name": "TestAgent",
            "scenario_name": "Date Test",
            "success": True,
            "tool_calls": [],
        }
    )

    dates = storage.get_available_dates()

    assert len(dates) == 1


def test_trace_count(tmp_path):
    storage = TraceStorage(tmp_path / "data")

    storage.save_trace(
        {
            "test_id": "TEST_COUNT_001",
            "success": True,
        }
    )

    assert storage.get_trace_count() == 1


def test_delete_trace(tmp_path):
    storage = TraceStorage(tmp_path / "data")

    storage.save_trace(
        {
            "test_id": "TEST_DELETE_001",
            "success": True,
        }
    )

    assert storage.load_trace("TEST_DELETE_001") is not None

    deleted = storage.delete_trace(
        "TEST_DELETE_001"
    )

    assert deleted is True
    assert storage.load_trace("TEST_DELETE_001") is None