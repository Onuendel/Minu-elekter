"""Prepare a dashboard data snapshot from exported Sheets rows; no remote writes."""
import argparse
import copy
import json
from pathlib import Path
from decimal import Decimal
from refresh_core import datetime, TZ, number, cost
from sheet_plan import inspect


def update_snapshot(snapshot, rows, first_row, day, now):
    if now.tzinfo is None or day >= now.astimezone(TZ).date().isoformat():
        raise ValueError('Only completed Tallinn calendar days are allowed')
    indexed, complete = inspect(rows, first_row)
    if complete != [day]:
        raise ValueError('Supply exactly one complete day of actual hourly measurements')
    if len(indexed) != len(rows) or any(
        datetime.fromisoformat(r['start']).astimezone(TZ).date().isoformat() != day
        for r in indexed.values()
    ):
        raise ValueError('Rows outside requested day')
    if int(day[:4]) != snapshot['year']:
        raise ValueError('Dashboard year mismatch')
    total = Decimal(0)
    totals = dict.fromkeys(('contractCost', 'spotCost', 'result'), Decimal(0))
    all_night = True
    for r in indexed.values():
        raw = r['raw']
        if raw[2] not in ('Päev', 'Öö'):
            raise ValueError('Unknown tariff')
        amounts = cost(r['kwh'], raw[5], raw[8], raw[6])
        expected = (number(raw[5]) + number(raw[6]),
                    number(raw[5]) + number(raw[6]) - number(raw[8]), amounts['result'])
        for column, value in zip((7, 9, 10), expected):
            if abs(number(raw[column]) - value) > Decimal('0.0000001'):
                raise ValueError('Sheet price or cost columns disagree')
        total += r['kwh']
        all_night = all_night and raw[2] == 'Öö'
        for key in totals:
            totals[key] += amounts[key]
    data = copy.deepcopy(snapshot)
    days = {d['date']: d for d in data['days']}
    if len(days) != len(data['days']):
        raise ValueError('Duplicate dashboard day')
    days[day] = {'date': day, 'consumption': float(total), 'allNight': all_night,
                 **{k: float(v) for k, v in totals.items()}}
    data['days'] = [days[k] for k in sorted(days)]
    cumulative = Decimal(0)
    for d in data['days']:
        cumulative += number(d['result'])
        d['cumulative'] = float(cumulative)
    data.update(lastComplete=data['days'][-1]['date'] + 'T23:00:00',
                completeDays=len(days), netResult=float(cumulative),
                totalConsumption=float(sum(number(d['consumption']) for d in days.values())),
                contractCheaperDays=sum(d['result'] > 0 for d in days.values()),
                spotCheaperDays=sum(d['result'] < 0 for d in days.values()))
    for m in data['months']:
        selected = [d for d in days.values() if int(d['date'][5:7]) == m['month']]
        m.update(days=len(selected),
                 result=float(sum(number(d['result']) for d in selected)) if selected else None,
                 consumption=float(sum(number(d['consumption']) for d in selected)) if selected else None)
    populated = [m for m in data['months'] if m['days']]
    data['bestMonth'] = copy.deepcopy(max(populated, key=lambda m: m['result']))
    data['worstMonth'] = copy.deepcopy(min(populated, key=lambda m: m['result']))
    return data


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('snapshot', 'sheet-values', 'day', 'now', 'output'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--first-row', type=int, required=True)
    args = parser.parse_args()
    result = update_snapshot(json.loads(Path(args.snapshot).read_text()),
                             json.loads(Path(args.sheet_values).read_text()),
                             args.first_row, args.day, datetime.fromisoformat(args.now))
    # Never replace an existing snapshot or source file implicitly.
    with Path(args.output).open('x') as output:
        json.dump(result, output, ensure_ascii=False, indent=2)
