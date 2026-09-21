"""Bounded, privacy-safe metric aggregation and diagnostic rotation."""

import json
import pathlib
import sys
import unittest
import uuid


sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from observability import Metrics


class MetricsTests(unittest.TestCase):
    def test_global_sample_cap_and_result_breakdown(self):
        metrics = Metrics(maximum=3)
        metrics.observe("old", "total", 0.001, result="success")
        metrics.observe("write", "total", 0.002, result="success")
        metrics.observe("write", "total", 0.003, result="idempotent_replay")
        metrics.observe("write", "total", 0.004, result="version_conflict")

        snapshot = metrics.snapshot()
        self.assertNotIn("old", snapshot["operations"])
        total = snapshot["operations"]["write"]["total"]
        self.assertEqual(total["samples"], 3)
        self.assertEqual(total["byResult"]["idempotent_replay"]["samples"], 1)
        self.assertAlmostEqual(total["errorRate"], 1 / 3, places=6)

    def test_flush_rotates_without_leaking_dimensions(self):
        folder = (
            pathlib.Path(__file__).resolve().parents[1]
            / "test-results"
            / ("metrics-" + uuid.uuid4().hex)
        )
        folder.mkdir(parents=True)
        target = folder / "metrics.jsonl"
        metrics = Metrics(target, maximum_log_bytes=1)
        metrics.observe("mods.search", "sql", 0.001, result="success", entries=48)
        metrics.flush()
        metrics.flush()

        self.assertTrue(target.exists())
        self.assertTrue(target.with_suffix(".jsonl.1").exists())
        payload = json.loads(target.read_text(encoding="utf-8"))
        self.assertIn("mods.search", payload["operations"])
        self.assertNotIn("requestBody", target.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
