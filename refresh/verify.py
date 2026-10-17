from refresh_core import *
import json
from pathlib import Path

source = json.loads(Path(__file__).with_name('sample.json').read_text())
points = [{'start': datetime.strptime(r[1], '%d.%m.%Y %H:%M').replace(tzinfo=TZ).isoformat(),
           'duration_minutes': 60, 'kwh': r[3], 'actual': r[4] == 'Tegelik'} for r in source]
rows = normalize_day('2026-09-08', points, 17.313)
assert len(rows) == 24
assert plan_upserts(rows, rows) == []
assert len(plan_upserts([], rows)) == 24
for day, count in [('2026-03-29', 23), ('2026-10-25', 25)]:
    p = [{'start': (h + timedelta(minutes=m)).isoformat(), 'duration_minutes': 15,
          'kwh': 0.25, 'actual': True} for h in hours(day) for m in (0,15,30,45)]
    assert len(normalize_day(day, p, count)) == count
for invalid in [points[:-1], points + points[:1], [{**points[0], 'actual': False}] + points[1:]]:
    try:
        normalize_day('2026-09-08', invalid, 17.313)
    except ValueError:
        pass
    else:
        raise AssertionError('Invalid data accepted')
assert pending_days('2026-09-07', {'2026-09-08'}, datetime(2026,9,9,12,tzinfo=UTC)) == ['2026-09-07']
assert cost(1, 20, 12.3)['result'] == Decimal('0.0817')
print('PASS: live day total, idempotency, insert planning, DST 23/25 hours, 15-minute aggregation, missing/duplicate/non-actual rejection, gap detection, margin calculation')
