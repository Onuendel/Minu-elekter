import unittest
from copy import deepcopy
from datetime import datetime
from dashboard_snapshot import update_snapshot
from refresh_core import TZ


class DashboardSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = {
            'year': 2026,
            'lastComplete': '2026-09-08T23:00:00',
            'completeDays': 1,
            'contractCheaperDays': 0,
            'spotCheaperDays': 1,
            'netResult': -0.1,
            'totalConsumption': 2.0,
            'bestMonth': {},
            'worstMonth': {},
            'months': [
                {'month': month, 'name': str(month), 'days': 1 if month == 9 else 0,
                 'result': -0.1 if month == 9 else None,
                 'consumption': 2.0 if month == 9 else None}
                for month in range(1, 13)
            ],
            'days': [{
                'date': '2026-09-08', 'result': -0.1, 'consumption': 2.0,
                'contractCost': 0.24, 'spotCost': 0.14,
                'allNight': False, 'cumulative': -0.1
            }],
        }
        self.rows = []
        for hour in range(24):
            tariff = 'Öö' if hour < 7 or hour >= 22 else 'Päev'
            self.rows.append([
                hour + 1, f'09.09.2026 {hour:02d}:00', tariff, 1, 'Tegelik',
                10, 0.5, 10.5, 12, -1.5, -0.015
            ])
        self.now = datetime(2026, 9, 10, 12, tzinfo=TZ)

    def test_updates_once_and_recalculates_totals(self):
        result = update_snapshot(self.snapshot, self.rows, 1, '2026-09-09', self.now)
        self.assertEqual(result['lastComplete'], '2026-09-09T23:00:00')
        self.assertEqual(result['completeDays'], 2)
        self.assertEqual(result['totalConsumption'], 26)
        self.assertAlmostEqual(result['netResult'], -0.46)
        self.assertEqual(result['days'][-1]['consumption'], 24)
        self.assertEqual(result['months'][8]['days'], 2)
        self.assertEqual(
            update_snapshot(result, self.rows, 1, '2026-09-09', self.now),
            result,
        )

    def test_rejects_forecast_and_inconsistent_cost(self):
        for column, value in ((4, 'Prognoos'), (10, 1)):
            rows = deepcopy(self.rows)
            rows[0][column] = value
            with self.assertRaises(ValueError):
                update_snapshot(self.snapshot, rows, 1, '2026-09-09', self.now)


if __name__ == '__main__':
    unittest.main()
