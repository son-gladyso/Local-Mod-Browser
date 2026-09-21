import pathlib
import sys
import threading
import time
import unittest


sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from write_scheduler import FairWriteGate


class FairWriteGateTests(unittest.TestCase):
    def test_four_foreground_writes_then_background(self):
        gate = FairWriteGate(foreground_ratio=4, background_max_wait=10)
        order = []
        ready = threading.Barrier(7)
        gate.acquire()

        def enter(label, background):
            ready.wait()
            gate.acquire(background=background)
            try:
                order.append(label)
                time.sleep(0.005)
            finally:
                gate.release()

        threads = [
            threading.Thread(target=enter, args=("background", True)),
            *[
                threading.Thread(target=enter, args=(f"foreground-{index}", False))
                for index in range(5)
            ],
        ]
        for thread in threads:
            thread.start()
        ready.wait()
        time.sleep(0.02)
        gate.release()
        for thread in threads:
            thread.join(2)
        self.assertLessEqual(order.index("background"), 4, order)
        self.assertTrue(
            all(
                label.startswith("foreground-")
                for label in order[: order.index("background")]
            )
        )

    def test_gate_is_reentrant_for_legacy_delegation(self):
        gate = FairWriteGate()
        gate.acquire()
        gate.acquire(background=True)
        gate.release()
        gate.release()

    def test_waiters_are_fifo_within_each_class(self):
        gate = FairWriteGate(foreground_ratio=2, background_max_wait=10)
        order = []
        gate.acquire()

        def enter(label, background=False):
            gate.acquire(background=background)
            try:
                order.append(label)
            finally:
                gate.release()

        threads = []
        expected_foreground = 0
        expected_background = 0
        for label, background in [
            ("foreground-1", False),
            ("foreground-2", False),
            ("background-1", True),
            ("background-2", True),
        ]:
            thread = threading.Thread(target=enter, args=(label, background))
            thread.start()
            threads.append(thread)
            deadline = time.monotonic() + 1
            if background:
                expected_background += 1
                expected = expected_background
            else:
                expected_foreground += 1
                expected = expected_foreground
            while time.monotonic() < deadline:
                waiting = (
                    gate.background_waiters if background else gate.foreground_waiters
                )
                if waiting >= expected:
                    break
                time.sleep(0.001)
        gate.release()
        for thread in threads:
            thread.join(2)
        self.assertLess(order.index("foreground-1"), order.index("foreground-2"))
        self.assertLess(order.index("background-1"), order.index("background-2"))

    def test_aged_background_waiters_yield_after_one_batch(self):
        gate = FairWriteGate(foreground_ratio=4, background_max_wait=0.01)
        order = []
        gate.acquire()

        def enter(label, background):
            gate.acquire(background=background)
            try:
                order.append(label)
            finally:
                gate.release()

        threads = []
        for label, background, expected in (
            ("background-1", True, 1),
            ("background-2", True, 2),
            ("foreground", False, 1),
        ):
            thread = threading.Thread(target=enter, args=(label, background))
            thread.start()
            threads.append(thread)
            deadline = time.monotonic() + 1
            while time.monotonic() < deadline:
                waiting = (
                    gate.background_waiters if background else gate.foreground_waiters
                )
                if waiting >= expected:
                    break
                time.sleep(0.001)

        time.sleep(0.02)
        gate.release()
        for thread in threads:
            thread.join(2)
            self.assertFalse(thread.is_alive())
        self.assertEqual(order, ["background-1", "foreground", "background-2"])
