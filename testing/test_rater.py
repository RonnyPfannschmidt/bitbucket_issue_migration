
import pytest
import mock
from migrate_to_github.utils.poster import Limiter
from datetime import datetime


@pytest.fixture
def time():
    return mock.Mock()


@pytest.fixture
def limiter(time):
    return Limiter(do_sleep=time.sleep, current_utctime=time.utcnow)


def test_initial_nowait(limiter, time):
    assert limiter.wait_seconds == 0
    limiter.wait_before_request()
    time.sleep.assert_called_with(0)


def test_wait_needed(limiter, time):
    time.utcnow.return_value = datetime.utcfromtimestamp(10)

    limiter.record_rate_limit(remaining=4, reset_timestamp=20)
    assert limiter.wait_seconds == pytest.approx(2.25)
