import tempfile
import unittest
from pathlib import Path

from scripts.generate_pulse_table import END, START, parse_log, render_table, update_readme

SAMPLE_LOG = """# heading
- 2026-08-25 04:23:30 UTC - automated profile pulse 1/4
- 2026-08-25 04:23:30 UTC - automated profile pulse 2/4
- 2026-08-25 04:23:30 UTC - automated profile pulse 3/4
- 2026-08-25 04:23:30 UTC - automated profile pulse 4/4
- 2026-08-26 04:24:16 UTC - automated profile pulse 1/2
- 2026-08-26 04:24:16 UTC - automated profile pulse 2/2
"""


class PulseTableTests(unittest.TestCase):
    def test_parse_log_groups_by_date_most_recent_first(self) -> None:
        rows = parse_log(SAMPLE_LOG)

        self.assertEqual(rows, [("2026-08-26", "04:24:16", 2), ("2026-08-25", "04:23:30", 4)])

    def test_parse_log_ignores_unrelated_lines(self) -> None:
        rows = parse_log("# heading\nsome other note\n")

        self.assertEqual(rows, [])

    def test_render_table_contains_rows(self) -> None:
        table = render_table(parse_log(SAMPLE_LOG))

        self.assertIn("| 2026-08-26 | 2 | 04:24:16 |", table)
        self.assertIn("| 2026-08-25 | 4 | 04:23:30 |", table)

    def test_render_table_handles_empty_log(self) -> None:
        self.assertIn("No automated pulses", render_table([]))

    def test_updates_only_the_marked_section(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            readme = Path(directory) / "README.md"
            readme.write_text(f"before\n{START}\nold\n{END}\nafter\n", encoding="utf-8")

            changed = update_readme(readme, "new table")

            self.assertTrue(changed)
            self.assertEqual(
                readme.read_text(encoding="utf-8"),
                f"before\n{START}\nnew table\n{END}\nafter\n",
            )
            self.assertFalse(update_readme(readme, "new table"))


if __name__ == "__main__":
    unittest.main()
