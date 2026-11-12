"""
test_rebalance.py
งานของ: คนที่ 3

ใช้ตัวอย่างวงแหวนเล็กจากโจทย์ หัวข้อ 9.1 (เหมือน test_hashring.py) มาตรวจ
add_building / remove_building แบบครบวงจร (ring + registry ทำงานร่วมกัน)
"""

import unittest
from copy import deepcopy
from unittest.mock import patch

from hashring import HashRing
from guest import GuestRegistry
import rebalance


class RebalanceTestCase(unittest.TestCase):
    """เครื่องมือช่วยตรวจข้อมูลจริง เทียบกับรายงานและดัชนีค้นหา"""

    def addresses(self):
        return {
            code: self.registry.find_by_guest_code(*code)
            for code in self.registry.all_guest_codes()
        }

    def snapshot(self):
        return deepcopy((
            self.ring.points, self.ring.nodes, self.ring.v,
            self.registry.by_guest_code, self.registry.by_address,
        ))

    def assert_migration(self, before, report):
        after = self.addresses()
        self.assertTrue(report.accepted)
        self.assertEqual(set(after), set(before))
        self.assertEqual(self.registry.guest_count(), len(before))
        self.assertEqual(len(self.registry.by_address), len(before))

        changed = {code for code in before if before[code][0] != after[code][0]}
        self.assertEqual(report.moved_count, len(changed))
        self.assertEqual(len(report.moves), len(changed))
        self.assertEqual({(m.c, m.s) for m in report.moves}, changed)
        if before:
            self.assertAlmostEqual(report.move_rate, len(changed) / len(before))
        else:
            self.assertIsNone(report.move_rate)

        for code, (node, room) in after.items():
            self.assertEqual(room, before[code][1])
            self.assertEqual(node, self.ring.get_owner_of_guest(*code)[1])
            self.assertEqual(self.registry.find_by_address(node, room), code)
            if code in changed:
                self.assertIsNone(self.registry.find_by_address(*before[code]))
        for move in report.moves:
            code = (move.c, move.s)
            self.assertEqual((move.old_node_id, move.room_no), before[code])
            self.assertEqual((move.new_node_id, move.room_no), after[code])

    def assert_rejected(self, operation, node_id):
        before = self.snapshot()
        report = operation(self.ring, self.registry, node_id)
        self.assertFalse(report.accepted)
        self.assertTrue(report.reason)
        self.assertEqual(report.moved_count, 0)
        self.assertEqual(report.moves, [])
        if self.registry.guest_count():
            self.assertEqual(report.move_rate, 0.0)
        else:
            self.assertIsNone(report.move_rate)
        self.assertEqual(self.snapshot(), before)


class TestRebalanceWithSpecExample(RebalanceTestCase):
    def setUp(self):
        positions = {
            "node:A:0": 20, "node:B:0": 50,
            "node:C:0": 80, "node:D:0": 35,
        }
        positions.update({
            f"guest:1:{s}": position
            for s, position in enumerate([10, 20, 25, 35, 50, 70, 90], 1)
        })
        patcher = patch("hashring.hash_to_position", side_effect=positions.__getitem__)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.ring = HashRing(1)
        self.registry = GuestRegistry()
        for node in "ABC":
            self.ring.add_node(node)
        for s in range(1, 8):
            ok, reason = self.registry.add_guest(1, s, self.ring.get_owner_of_guest(1, s)[1])
            self.assertTrue(ok, reason)
        self.before = self.addresses()
        self.assertEqual([self.before[(1, s)][0] for s in range(1, 8)],
                         ["A", "A", "B", "B", "B", "C", "A"])

    def test_add_building_migrates_only_two(self):
        """เพิ่ม D ที่ตำแหน่ง 35 ต้องมีคนย้ายเข้า D เท่านั้น 2 คน คนอื่นไม่ขยับ"""
        report = rebalance.add_building(self.ring, self.registry, "D")
        self.assert_migration(self.before, report)
        self.assertEqual(report.moved_count, 2)
        self.assertEqual([self.registry.find_by_guest_code(1, s)[0] for s in range(1, 8)],
                         ["A", "A", "D", "D", "B", "C", "A"])
        self.assertTrue(all(move.new_node_id == "D" for move in report.moves))

    def test_remove_building_migrates_only_three(self):
        """ลบ B จากสถานะเริ่มต้น ต้องมีคนย้าย 3 คน (เฉพาะที่เคยอยู่ B) อาคารอื่นไม่ขยับ"""
        report = rebalance.remove_building(self.ring, self.registry, "B")
        self.assert_migration(self.before, report)
        self.assertEqual(report.moved_count, 3)
        self.assertEqual([self.registry.find_by_guest_code(1, s)[0] for s in range(1, 8)],
                         ["A", "A", "C", "C", "C", "C", "A"])
        self.assertTrue(all(move.old_node_id == "B" for move in report.moves))

    def test_room_no_unchanged_after_migration(self):
        """room_no ของทุกคนที่ย้ายต้องเท่าเดิม เปลี่ยนแค่ node_id"""
        rebalance.add_building(self.ring, self.registry, "D")
        rebalance.remove_building(self.ring, self.registry, "B")
        for code, (_, room) in self.before.items():
            self.assertEqual(self.registry.find_by_guest_code(*code)[1], room)

    def test_guest_count_invariant(self):
        """จำนวนแขกรวมในระบบต้องไม่เพิ่มไม่ลดหลังเพิ่ม/ลบอาคาร"""
        for operation, node in [(rebalance.add_building, "D"),
                                (rebalance.remove_building, "B")]:
            before = self.addresses()
            report = operation(self.ring, self.registry, node)
            self.assert_migration(before, report)


class TestRebalanceEdgeCases(RebalanceTestCase):
    def setUp(self):
        self.ring = HashRing(3)
        self.ring.add_node("A")
        self.registry = GuestRegistry()
        self.registry.add_guest(1, 1, "A")

    def test_add_building_duplicate_rejected(self):
        self.assert_rejected(rebalance.add_building, "A")

    def test_remove_building_unknown_rejected(self):
        self.assert_rejected(rebalance.remove_building, "unknown")

    def test_remove_last_building_rejected(self):
        self.assert_rejected(rebalance.remove_building, "A")

    def test_remove_last_building_without_guests_rejected(self):
        self.registry = GuestRegistry()
        self.assert_rejected(rebalance.remove_building, "A")

    def test_zero_guests_move_rate_reported_as_none(self):
        """K = 0: รายงานจำนวนย้ายเป็น 0 และไม่คำนวณอัตรา (move_rate ควรเป็น None)"""
        self.registry = GuestRegistry()
        for operation in [rebalance.add_building, rebalance.remove_building]:
            report = operation(self.ring, self.registry, "B")
            self.assert_migration({}, report)
            self.assertEqual(report.moved_count, 0)
            self.assertEqual(report.moves, [])

    def test_rejections_without_guests(self):
        self.registry = GuestRegistry()
        self.assert_rejected(rebalance.add_building, "A")
        self.assert_rejected(rebalance.remove_building, "unknown")

    def test_remove_empty_building_with_guests_elsewhere(self):
        self.ring.points = [(20, "A", 0), (50, "B", 0)]
        self.ring.nodes = {"A", "B"}
        self.ring.v = 1
        with patch("hashring.hash_to_position", return_value=10):
            before = self.addresses()
            report = rebalance.remove_building(self.ring, self.registry, "B")
            self.assert_migration(before, report)
            self.assertEqual(report.moved_count, 0)
            self.assertEqual(report.move_rate, 0.0)


class TestRebalanceWithVirtualNodes(RebalanceTestCase):
    def setUp(self):
        self.ring = HashRing(8)
        self.registry = GuestRegistry()
        for node in "ABC":
            self.ring.add_node(node)
        for c in range(1, 6):
            for s in range(1, 101):
                ok, reason = self.registry.add_guest(c, s, self.ring.get_owner_of_guest(c, s)[1])
                self.assertTrue(ok, reason)

    def test_add_preserves_existing_points_and_moves_only_to_new_building(self):
        before = self.addresses()
        old_points = list(self.ring.points)
        report = rebalance.add_building(self.ring, self.registry, "D")
        self.assert_migration(before, report)
        self.assertGreater(report.moved_count, 0)
        self.assertTrue(all(move.new_node_id == "D" for move in report.moves))
        self.assertEqual([p for p in self.ring.points if p[1] != "D"], old_points)
        self.assertEqual(self.ring.point_count(), 4 * 8)
        self.assertEqual(self.ring.v, 8)

    def test_remove_preserves_other_buildings_and_their_points(self):
        before = self.addresses()
        keep_points = [p for p in self.ring.points if p[1] != "B"]
        expected_codes = {code for code, (node, _) in before.items() if node == "B"}
        report = rebalance.remove_building(self.ring, self.registry, "B")
        self.assert_migration(before, report)
        self.assertGreater(report.moved_count, 0)
        self.assertEqual({(m.c, m.s) for m in report.moves}, expected_codes)
        for code, address in before.items():
            if code not in expected_codes:
                self.assertEqual(self.registry.find_by_guest_code(*code), address)
        self.assertEqual(self.ring.points, keep_points)
        self.assertNotIn("B", self.ring.nodes)
        self.assertEqual(self.ring.point_count(), 2 * 8)
        self.assertEqual(self.ring.v, 8)


if __name__ == "__main__":
    unittest.main()
