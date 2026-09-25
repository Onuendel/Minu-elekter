"""Minu Elekter: offline validation and write planning; no network or writes.

Input points are normalized by a future provider adapter. Each point needs
an offset-aware start, duration_minutes (15 or 60), numeric kwh and actual=True.
No Elektrilevi response schema or authentication implementation is assumed.
"""
from datetime import datetime, date, time, timedelta, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

TZ = ZoneInfo('Europe/Tallinn')
UTC = timezone.utc

def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise ValueError('Numeric value required; blanks are not zero')
    result = Decimal(str(value))
    if not result.is_finite():
        raise ValueError('Finite value required')
    return result

def hours(day):
    day = date.fromisoformat(day)
    start = datetime.combine(day, time(), TZ).astimezone(UTC)
    end = datetime.combine(day + timedelta(days=1), time(), TZ).astimezone(UTC)
    result = []
    while start < end:
        result.append(start)
        start += timedelta(hours=1)
    return result

def normalize_day(day, points, expected_total):
    expected = hours(day)
    slots = {}
    for point in points:
        stamp = datetime.fromisoformat(point['start'])
        if stamp.tzinfo is None:
            raise ValueError('UTC offset required, especially at autumn DST')
        stamp = stamp.astimezone(UTC)
        duration = point['duration_minutes']
        if duration not in (15, 60) or stamp.second or stamp.microsecond or stamp.minute % duration:
            raise ValueError('Invalid interval alignment')
        if stamp.astimezone(TZ).date().isoformat() != day:
            raise ValueError('Point outside requested day')
        if point.get('actual') is not True:
            raise ValueError('Missing or non-actual measurements')
        energy = number(point['kwh'])
        if energy < 0:
            raise ValueError('Negative consumption')
        for offset in range(0, duration, 15):
            key = stamp + timedelta(minutes=offset)
            if key in slots:
                raise ValueError('Duplicate or overlapping measurement')
            slots[key] = energy / (duration // 15)
    required = {h + timedelta(minutes=m) for h in expected for m in (0, 15, 30, 45)}
    if set(slots) != required:
        raise ValueError('Incomplete day')
    rows = [{'start': h.isoformat(), 'localStart': h.astimezone(TZ).isoformat(),
             'kwh': sum(slots[h + timedelta(minutes=m)] for m in (0, 15, 30, 45))}
            for h in expected]
    if abs(sum(r['kwh'] for r in rows) - number(expected_total)) > Decimal('0.001'):
        raise ValueError('Daily total mismatch')
    return rows

def pending_days(first_day, complete_days, now):
    if now.tzinfo is None:
        raise ValueError('Offset-aware current time required')
    target = now.astimezone(TZ).date() - timedelta(days=1)
    cursor = date.fromisoformat(first_day)
    result = []
    while cursor <= target:
        if cursor.isoformat() not in complete_days:
            result.append(cursor.isoformat())
        cursor += timedelta(days=1)
    return result

def plan_upserts(existing, incoming):
    """UTC keys keep both autumn 03:00 hours distinct. Caller assigns sheet rows."""
    by_key = {}
    for row in existing:
        if row['start'] in by_key:
            raise ValueError('Duplicate masterdata key')
        by_key[row['start']] = row
    seen = set()
    changes = []
    for row in incoming:
        key = row['start']
        if key in seen:
            raise ValueError('Duplicate incoming key')
        seen.add(key)
        old = by_key.get(key)
        if old is None or old['kwh'] != row['kwh']:
            changes.append({'operation': 'update' if old else 'insert', 'before': old, 'after': row})
    return changes

def cost(kwh, spot_cents, contract_cents, margin_cents=Decimal('0.47')):
    # Caller supplies historical contract price; never rewrite it with today's rate.
    kwh, spot, contract, margin = map(number, (kwh, spot_cents, contract_cents, margin_cents))
    return {'contractCost': kwh * contract / 100,
            'spotCost': kwh * (spot + margin) / 100,
            'result': kwh * (spot + margin - contract) / 100}
