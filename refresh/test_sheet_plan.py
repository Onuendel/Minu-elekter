import unittest
import json
from pathlib import Path
from sheet_plan import inspect, make_plan, timestamp
from refresh_core import datetime, TZ, UTC

class SheetPlanTests(unittest.TestCase):
    def setUp(self):
        self.rows = json.loads(Path(__file__).with_name('sample.json').read_text())
        self.now = datetime(2026,9,9,12,tzinfo=UTC)

    def test_complete_real_sample(self):
        plan = make_plan(self.rows,6002,'2026-09-08',self.now)
        self.assertEqual(plan['missingDays'], [])
        self.assertEqual(plan['changes'], [])

    def test_blank_is_missing_but_zero_is_valid(self):
        self.rows[0][3] = None
        self.assertEqual(inspect(self.rows,6002)[1], [])
        self.rows[0][3] = 0
        self.assertEqual(inspect(self.rows,6002)[1], ['2026-09-08'])

    def test_ambiguous_and_nonexistent(self):
        for value in ['25.10.2026 03:00','29.03.2026 03:00']:
            with self.assertRaises(ValueError): timestamp(value)
        self.assertNotEqual(timestamp('2026-10-25T03:00:00+03:00'),timestamp('2026-10-25T03:00:00+02:00'))

    def test_duplicate(self):
        with self.assertRaises(ValueError): inspect(self.rows+self.rows[:1],6002)

    def test_precise_repair_and_repeat(self):
        points = [{'start': timestamp(r[1]).isoformat(), 'duration_minutes':60,
                   'kwh':r[3], 'actual':True} for r in self.rows]
        incoming = [{'date':'2026-09-08','total_kwh':17.313,'points':points}]
        self.rows[0][3] = None
        plan = make_plan(self.rows,6002,'2026-09-08',self.now,incoming)
        self.assertEqual(len(plan['changes']),1)
        self.assertEqual(plan['changes'][0]['range'], "'Data 2026'!D6002:E6002")
        self.rows[0][3:5] = plan['changes'][0]['after']
        self.assertEqual(make_plan(self.rows,6002,'2026-09-08',self.now,incoming)['changes'],[])

if __name__ == '__main__': unittest.main()
