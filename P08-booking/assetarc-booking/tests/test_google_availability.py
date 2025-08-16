import datetime
import os
import sys
from unittest.mock import patch

# Ensure the module under test can be imported when tests are executed
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import google_availability


def test_business_slots_excludes_busy_interval():
    busy = [
        {
            'start': '2024-01-01T12:00:00+02:00',
            'end': '2024-01-01T13:00:00+02:00',
        }
    ]
    with patch('google_availability.freebusy', return_value=busy):
        slots = google_availability.business_slots(
            '2024-01-01',
            '2024-01-01',
            'cal',
            'Africa/Johannesburg',
            '09:00-17:00',
        )
    # ensure busy period excluded
    for slot in slots:
        assert not (
            slot['start'] == '2024-01-01T12:00:00+02:00'
            or slot['end'] == '2024-01-01T13:00:00+02:00'
        )
    assert slots[0]['start'] == '2024-01-01T09:00:00+02:00'
    assert slots[-1]['end'] == '2024-01-01T17:00:00+02:00'
    # 8 possible slots in window minus 1 busy slot
    assert len(slots) == 7


def test_business_slots_window_and_boundaries():
    busy = [
        {
            'start': '2024-06-01T08:30:00+00:00',
            'end': '2024-06-01T09:00:00+00:00',
        },
        {
            'start': '2024-06-01T10:00:00+00:00',
            'end': '2024-06-01T11:00:00+00:00',
        },
    ]
    with patch('google_availability.freebusy', return_value=busy):
        slots = google_availability.business_slots(
            '2024-06-01',
            '2024-06-01',
            'cal',
            'UTC',
            '09:00-11:00',
        )
    assert slots == [
        {
            'start': '2024-06-01T09:00:00+00:00',
            'end': '2024-06-01T10:00:00+00:00',
        }
    ]
