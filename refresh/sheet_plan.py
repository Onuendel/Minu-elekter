"""Read exported Sheets values and prepare D:E changes. Never writes remotely."""
import argparse
import json
from collections import defaultdict
from pathlib import Path
from refresh_core import datetime, TZ, UTC, number, hours, normalize_day, pending_days

def timestamp(value):
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        dt = datetime.strptime(value, '%d.%m.%Y %H:%M')
    if dt.tzinfo is None:
        candidates = {dt.replace(tzinfo=TZ, fold=f).astimezone(UTC) for f in (0, 1)
                      if dt.replace(tzinfo=TZ, fold=f).astimezone(UTC).astimezone(TZ).replace(tzinfo=None) == dt}
        if len(candidates) != 1:
            raise ValueError('Ambiguous or nonexistent local hour: explicit offset required')
        dt = candidates.pop()
    dt = dt.astimezone(UTC)
    if dt.minute or dt.second or dt.microsecond:
        raise ValueError('Masterdata must contain aligned hourly rows')
    return dt

def inspect(values, first_row):
    indexed, days = {}, defaultdict(list)
    for rownum, row in enumerate(values, first_row):
        if not row or all(v is None or v == '' for v in row):
            continue
        if len(row) < 2 or not isinstance(row[1], str):
            raise ValueError(f'Row {rownum}: timestamp must be text')
        stamp = timestamp(row[1])
        key = stamp.isoformat()
        if key in indexed:
            raise ValueError(f'Row {rownum}: duplicate timestamp')
        padded = row + [None] * max(0, 11-len(row))
        quantity = padded[3]
        if quantity not in (None, ''):
            quantity = number(quantity)
            if quantity < 0:
                raise ValueError(f'Row {rownum}: negative consumption')
        else:
            quantity = None
        item = {'row': rownum, 'start': key, 'kwh': quantity, 'actual': padded[4] == 'Tegelik', 'raw': padded}
        indexed[key] = item
        days[stamp.astimezone(TZ).date().isoformat()].append(item)
    complete = []
    for day, items in sorted(days.items()):
        if ({r['start'] for r in items} == {h.isoformat() for h in hours(day)}
                and all(r['kwh'] is not None and r['actual'] for r in items)):
            complete.append(day)
    return indexed, complete

def make_plan(values, first_row, first_day, now, incoming=None):
    indexed, complete = inspect(values, first_row)
    missing = pending_days(first_day, set(complete), now)
    changes = []
    for batch in incoming or []:
        day = batch['date']
        if day not in pending_days(first_day, set(), now):
            raise ValueError('Incoming day is outside the allowed completed-day period')
        rows = normalize_day(day, batch['points'], batch['total_kwh'])
        for row in rows:
            old = indexed.get(row['start'])
            if old is None:
                raise ValueError('No preallocated masterdata row: insertion needs a separate reviewed plan')
            if old['kwh'] != row['kwh'] or not old['actual']:
                changes.append({'range': f"'Data 2026'!D{old['row']}:E{old['row']}",
                                'before': old['raw'][3:5],
                                'after': [float(row['kwh']), 'Tegelik']})
                old['kwh'], old['actual'] = row['kwh'], True
    return {'mode': 'dry-run', 'lastCompleteDay': max(complete, default=None),
            'missingDays': missing, 'changes': changes,
            'note': 'Consumption-only proposal. Prices/formulas/dashboard and remote writes are not performed.'}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sheet-values', required=True, help='JSON array of A:K rows, without headers')
    parser.add_argument('--first-row', required=True, type=int)
    parser.add_argument('--first-day', required=True)
    parser.add_argument('--now', required=True, help='ISO timestamp with UTC offset')
    parser.add_argument('--incoming', help='JSON list of normalized daily measurement batches')
    args = parser.parse_args()
    result = make_plan(json.loads(Path(args.sheet_values).read_text()), args.first_row,
                       args.first_day, datetime.fromisoformat(args.now),
                       json.loads(Path(args.incoming).read_text()) if args.incoming else None)
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))

if __name__ == '__main__':
    main()
