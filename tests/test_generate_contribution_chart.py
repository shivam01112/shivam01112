import unittest

from scripts.generate_contribution_chart import render_svg, weekly_totals


def make_calendar(day_counts: list[int]) -> dict:
    days = [{"date": f"2026-01-{i + 1:02d}", "contributionCount": count} for i, count in enumerate(day_counts)]
    weeks = [{"contributionDays": days[i : i + 7]} for i in range(0, len(days), 7)]
    return {"totalContributions": sum(day_counts), "weeks": weeks}


class ContributionChartTests(unittest.TestCase):
    def test_weekly_totals_sums_each_week(self) -> None:
        calendar = make_calendar([1, 2, 3, 4, 5, 6, 7, 0, 0, 0, 0, 0, 0, 1])

        totals = weekly_totals(calendar, weeks=12)

        self.assertEqual(totals[0], ("2026-01-07", 28))
        self.assertEqual(totals[1], ("2026-01-14", 1))

    def test_weekly_totals_caps_to_requested_window(self) -> None:
        calendar = make_calendar([1] * 7 * 20)

        totals = weekly_totals(calendar, weeks=12)

        self.assertEqual(len(totals), 12)

    def test_render_svg_includes_totals_and_labels(self) -> None:
        totals = [("2026-01-07", 10), ("2026-01-14", 0)]

        svg = render_svg(totals, total_contributions=10)

        self.assertIn("<svg", svg)
        self.assertIn("10 total (last year)", svg)
        self.assertIn("01-07", svg)

    def test_render_svg_handles_no_data_without_crashing(self) -> None:
        svg = render_svg([], total_contributions=0)

        self.assertIn("<svg", svg)


if __name__ == "__main__":
    unittest.main()
