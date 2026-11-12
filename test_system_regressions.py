"""Regression tests for input handling, reports, initialization, and experiment reuse."""
import csv
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout

from hotel_system import HotelSystem, run_cli
from hashring import HashRing
import experiments
import rebalance


def run_menu(inputs):
    output = io.StringIO()
    with patch("builtins.input", side_effect=inputs), redirect_stdout(output):
        run_cli()
    return output.getvalue()


class TestSystemRegressions(unittest.TestCase):
    def test_invalid_ring_and_initial_buildings(self):
        for v in (0, -1, True, 1.5, "8"):
            with self.subTest(v=v), self.assertRaises(ValueError):
                HashRing(v)
        for nodes in ([], [""], ["A", "A"], ["A B"], [None]):
            with self.subTest(nodes=nodes), self.assertRaises(ValueError):
                HotelSystem(nodes, 8)

    def test_invalid_building_operations_preserve_state(self):
        h = HotelSystem(["A"], 8)
        h.init_guests({1: 10})
        before = h.list_occupied_rooms()
        points = list(h.ring.points)
        for node in ("", " ", "A B", None, []):
            self.assertFalse(h.add_building(node).accepted)
            self.assertFalse(h.remove_building(node).accepted)
        self.assertEqual(h.ring.points, points)
        self.assertEqual(h.list_occupied_rooms(), before)

    def test_initial_channels_start_at_one(self):
        h = HotelSystem(["A", "B"], 8)
        h.init_guests({1: 3, 2: 2, 3: 0})
        self.assertEqual(set(h.registry.all_guest_codes()), {(1, 1), (1, 2), (1, 3), (2, 1), (2, 2)})

    def test_initialization_rejects_entire_invalid_set(self):
        h = HotelSystem(["A"], 8)
        h.init_guests({2: 1})
        before = h.list_occupied_rooms()
        for channels in ({1: 3, 2: 1}, {1: 3, 2: -1}, {1: 3, 0: 2}, {1: True}):
            with self.subTest(channels=channels), self.assertRaises(ValueError):
                h.init_guests(channels)
            self.assertEqual(h.list_occupied_rooms(), before)

    def test_cv_matches_population_standard_deviation_over_mean(self):
        h = HotelSystem(["A", "B"], 8)
        needed = {"A": 3, "B": 1}
        for s in range(1, 1000):
            node = h.ring.get_owner_of_guest(1, s)[1]
            if needed[node]:
                h.add_guest(1, s)
                needed[node] -= 1
            if not any(needed.values()):
                break
        ok, data, _ = h.load_balance_report()
        self.assertTrue(ok)
        self.assertEqual(data["per_building"], {"A": 3, "B": 1})
        self.assertEqual((data["mean"], data["std"], data["cv"]), (2, 1, 0.5))

    def test_empty_statistics_include_all_buildings(self):
        h = HotelSystem(["B", "A"], 8)
        _, data, _ = h.load_balance_report()
        self.assertEqual(data["per_building"], {"A": 0, "B": 0})
        self.assertEqual([data[k] for k in ("max", "min", "mean", "std")], [0] * 4)
        self.assertIsNone(data["cv"])

    def test_listing_and_counts_cover_every_guest(self):
        h = HotelSystem(list("JIHGFEDCBA"), 8)
        h.init_guests({1: 500, 2: 500})
        rooms = h.list_occupied_rooms()
        self.assertEqual(rooms, sorted(rooms))
        self.assertEqual(sum(h.building_loads().values()), 1000)
        self.assertEqual(len(rooms), 1000)

    def test_invalid_remove_does_not_alias_guest_one(self):
        h = HotelSystem(["A"], 8)
        h.add_guest(1, 1)
        for code in ((True, 1), (1.0, 1), ([], 1)):
            self.assertFalse(h.remove_guest(*code)[0])
            self.assertIsNone(h.find_by_guest(*code))
        self.assertEqual(h.find_by_guest(1, 1), ("A", 1))

    def test_experiments_call_production_rebalance(self):
        h = experiments.ConsistentHashSystem(["A", "B"], 8, "0")
        self.assertIsInstance(h, HotelSystem)
        h.init_guests({1: 100})
        with patch("rebalance.add_building", wraps=rebalance.add_building) as add:
            report = h.add_building("C")
        add.assert_called_once_with(h.ring, h.registry, "C")
        self.assertEqual(h.last_timing, report.timings)
        self.assertTrue(all(v >= 0 for v in h.last_timing.values()))
        with patch("rebalance.remove_building", wraps=rebalance.remove_building) as remove:
            h.remove_building("B")
        remove.assert_called_once_with(h.ring, h.registry, "B")

    def test_experiment_summary_uses_median_and_range(self):
        rows = [dict(experiment="A", K=1000, N=10, V=32, method="consistent",
                     round=i + 1, salt=i, place_s=t) for i, t in enumerate([1.0, 100.0, 3.0])]
        summary, = experiments.summarize_results(rows)
        self.assertEqual((summary["place_s_median"], summary["place_s_min"], summary["place_s_max"]), (3, 1, 100))
        self.assertEqual(summary["rounds"], 3)


class TestMenuRegressions(unittest.TestCase):
    def test_all_operations_before_initialization_are_rejected(self):
        out = run_menu([str(i) for i in range(2, 10)] + ["0"])
        self.assertEqual(out.count("กรุณาเริ่มระบบด้วยเมนู 1 ก่อน"), 8)

    def test_invalid_numbers_return_to_menu(self):
        out = run_menu(["1", "A", "²", "1", "A", "-1", "1", "A", "8", "0", "0"])
        self.assertEqual(out.count("FAILED:"), 2)
        self.assertIn("สร้างระบบสำเร็จ", out)

    def test_initial_channels_and_two_way_search(self):
        out = run_menu(["1", "A", "8", "2", "3", "2", "6", "1", "2 1", "6", "2", "A 2", "0"])
        self.assertIn("แขกทั้งหมด 5 คน", out)
        self.assertIn("แขก (2, 1) อยู่ที่อาคาร A ห้อง 2", out)
        self.assertIn("รหัสแขก (2, 1)", out)

    def test_malformed_pairs_and_multiple_spaces(self):
        out = run_menu(["1", "A", "8", "1", "1", "3", "1", "6", "1", "1 2 3",
                        "6", "2", "A", "6", "1", "1   1", "0"])
        self.assertEqual(out.count("FAILED:"), 3)
        self.assertIn("แขก (1, 1) อยู่ที่อาคาร A ห้อง 1", out)

    def test_zero_batch_is_no_change(self):
        out = run_menu(["1", "A", "8", "0", "2", "1", "1", "0", "7", "0"])
        self.assertNotIn("FAILED:", out)
        self.assertIn("ไม่มีการเปลี่ยนแปลง", out)
        self.assertIn("ทั้งหมด 0 ห้อง", out)

    def test_empty_load_report_shows_zero_values(self):
        out = run_menu(["1", "A B", "8", "0", "8", "0"])
        for text in ("อาคาร A: 0 คน", "อาคาร B: 0 คน", "max: 0", "std: 0", "ไม่คำนวณ CV"):
            self.assertIn(text, out)

    def test_migrations_display_count_rate_and_unchanged_room(self):
        reference = HotelSystem(["A", "B"], 8)
        reference.init_guests({1: 100})
        report = reference.add_building("C")
        self.assertGreater(report.moved_count, 0)
        out = run_menu(["1", "A B", "8", "1", "100", "4", "C", "0"])
        self.assertIn(f"ย้ายทั้งหมด {report.moved_count} คน", out)
        self.assertIn(f"{report.move_rate:.2%}", out)
        move = report.moves[0]
        self.assertIn(f"({move.c}, {move.s}): {move.old_node_id} -> C, ห้อง {move.room_no}", out)

    def test_reset_clears_migration_report(self):
        out = run_menu(["1", "A B", "8", "1", "20", "4", "C", "1", "X", "8", "0", "9", "2", "0"])
        self.assertIn("ไม่มี Migration Report", out)
        self.assertNotIn("เขียนไฟล์ CSV แล้ว", out)

    def test_invalid_restart_preserves_previous_system(self):
        out = run_menu(["1", "A", "8", "1", "1", "1", "B B", "8", "6", "1", "1 1", "0"])
        self.assertIn("รหัสอาคารซ้ำ", out)
        self.assertIn("แขก (1, 1) อยู่ที่อาคาร A ห้อง 1", out)

    def test_bad_export_path_returns_to_menu(self):
        out = run_menu(["1", "A", "8", "0", "9", "1", "path_that_does_not_exist/guests.csv", "7", "0"])
        self.assertIn("เขียนไฟล์ไม่สำเร็จ", out)
        self.assertIn("ทั้งหมด 0 ห้อง", out)

    def test_end_of_input_exits_cleanly(self):
        out = io.StringIO()
        with patch("builtins.input", side_effect=EOFError), redirect_stdout(out):
            run_cli()
        self.assertIn("ออกจากโปรแกรม", out.getvalue())

    def test_main_process_exports_complete_csv(self):
        project = Path(__file__).resolve().parent
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "guests.csv"
            inputs = ["1", "A", "8", "1", "5", "9", "1", str(path), "0"]
            result = subprocess.run([sys.executable, "-X", "utf8", str(project / "Distributed_Hilbert’s_Hotel.py")],
                                    input="\n".join(inputs) + "\n", text=True, encoding="utf-8",
                                    capture_output=True, cwd=project, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn("FAILED:", result.stdout)
            with path.open(encoding="utf-8", newline="") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), 5)
            self.assertEqual([int(row["room_no"]) for row in rows], [1, 3, 6, 10, 15])


if __name__ == "__main__":
    unittest.main()
