from notification_service import BuildEvent, notification_for


def test_failed_build_is_not_published():
    event = BuildEvent("acct-1", "ledger", "r17", "failed", "lint error")
    assert notification_for(event) is None


def test_successful_release_contains_diagnostics():
    event = BuildEvent("acct-1", "ledger", "r18", "succeeded", "12 checks passed")
    assert notification_for(event) == {
        "project": "ledger",
        "release": "r18",
        "message": "Release r18 is ready",
        "diagnostics": "12 checks passed",
    }
