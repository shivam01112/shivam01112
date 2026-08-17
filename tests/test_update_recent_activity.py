import tempfile
import unittest
from pathlib import Path

from scripts.update_recent_activity import END, START, render, update_readme


class RecentActivityTests(unittest.TestCase):
    def test_renders_supported_events(self) -> None:
        events = [
            {
                "type": "PushEvent",
                "repo": {"name": "shivam01112/demo"},
                "payload": {"commits": [{}, {}]},
            },
            {
                "type": "CreateEvent",
                "repo": {"name": "shivam01112/demo"},
                "payload": {"ref_type": "branch", "ref": "feature/ui"},
            },
        ]

        activity = render(events)

        self.assertIn("Pushed **2 commits**", activity)
        self.assertIn("Created branch `feature/ui`", activity)
        self.assertIn("https://github.com/shivam01112/demo", activity)

    def test_updates_only_the_marked_section(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            readme = Path(directory) / "README.md"
            readme.write_text(f"before\n{START}\nold\n{END}\nafter\n", encoding="utf-8")

            changed = update_readme(readme, "1. New activity")

            self.assertTrue(changed)
            self.assertEqual(
                readme.read_text(encoding="utf-8"),
                f"before\n{START}\n1. New activity\n{END}\nafter\n",
            )
            self.assertFalse(update_readme(readme, "1. New activity"))

    def test_handles_hidden_commit_counts_and_deduplicates(self) -> None:
        event = {
            "type": "PushEvent",
            "repo": {"name": "shivam01112/private-payload"},
            "payload": {},
        }

        activity = render([event, event])

        self.assertEqual(activity.count("Pushed updates"), 1)
        self.assertNotIn("0 commits", activity)


if __name__ == "__main__":
    unittest.main()
