import hashlib
import unittest

from hashring import RING_SIZE, HashRing, hash_to_position


def make_small_ring(points):
    """
    สร้างวงแหวนเล็กโดยกำหนดตำแหน่งเอง (ไม่พึ่ง SHA-256)
    points: list ของ (position, node_id, j)
    """
    ring = HashRing(1)
    ring.points = sorted(points)
    ring.nodes = {p[1] for p in points}
    return ring


def owner_id(ring, position):
    """get_owner คืน tuple (position, node_id, j) -> หยิบเฉพาะ node_id"""
    owner = ring.get_owner(position)
    return None if owner is None else owner[1]


class TestHashToPosition(unittest.TestCase):
    def test_matches_spec(self):
        # คำนวณตามกติกา: sha256 -> utf-8 -> 8 ไบต์แรก big-endian
        for key in ["guest:1:1", "node:A:0", "guest:999:12345", "node:ตึก:3"]:
            digest = hashlib.sha256(key.encode("utf-8")).digest()
            self.assertEqual(hash_to_position(key), int.from_bytes(digest[:8], "big"))

    def test_stable_constants(self):
        # ค่าตายตัว: ถ้าเทสนี้พัง แปลว่าแฮชไม่คงที่ข้ามการรัน/เปลี่ยนวิธีแฮช
        self.assertEqual(hash_to_position("guest:1:1"), 3062031282815716176)
        self.assertEqual(hash_to_position("node:A:0"), 18050195718888941696)

    def test_in_range(self):
        for i in range(1, 2000):
            pos = hash_to_position(f"guest:{i}:{i}")
            self.assertTrue(0 <= pos < RING_SIZE)

    def test_guest_and_node_keys_differ(self):
        self.assertNotEqual(hash_to_position("guest:1:1"), hash_to_position("node:1:1"))


class TestSmallRing(unittest.TestCase):
    """วงแหวนขนาด 100, V=1: A ที่ 20, B ที่ 50, C ที่ 80"""

    def setUp(self):
        self.ring = make_small_ring([(20, "A", 0), (50, "B", 0), (80, "C", 0)])

    def test_owner_table(self):
        expected = {
            0: "A", 10: "A", 20: "A",   # <= 20 -> A (>= ตรงจุดพอดีได้จุดนั้น)
            21: "B", 35: "B", 50: "B",
            51: "C", 70: "C", 80: "C",
            81: "A", 90: "A", 99: "A",  # เกินจุดสุดท้าย -> วนกลับ A
        }
        for position, node in expected.items():
            self.assertEqual(owner_id(self.ring, position), node, f"position={position}")

    def test_wraparound_90_is_A(self):
        self.assertEqual(owner_id(self.ring, 90), "A")

    def test_get_owner_returns_full_point(self):
        self.assertEqual(self.ring.get_owner(35), (50, "B", 0))
        self.assertEqual(self.ring.get_owner(90), (20, "A", 0))

    def test_empty_ring_returns_none(self):
        ring = HashRing(3)
        self.assertIsNone(ring.get_owner(123))
        self.assertIsNone(ring.get_owner_of_guest(1, 1))

    def test_single_point_owns_everything(self):
        ring = make_small_ring([(40, "A", 0)])
        for position in [0, 39, 40, 41, 99]:
            self.assertEqual(owner_id(ring, position), "A")


class TestCollision(unittest.TestCase):
    def test_same_position_sorted_by_node_id_then_j(self):
        ring = make_small_ring([(50, "B", 0), (50, "A", 1), (50, "A", 0), (80, "C", 0)])
        self.assertEqual(ring.points[:3], [(50, "A", 0), (50, "A", 1), (50, "B", 0)])
        # จุดแรกตามลำดับ (position, node_id, j) เป็นเจ้าของ
        self.assertEqual(ring.get_owner(50), (50, "A", 0))
        self.assertEqual(ring.get_owner(30), (50, "A", 0))
        self.assertEqual(ring.get_owner(51), (80, "C", 0))

    def test_collision_at_first_point_with_wraparound(self):
        ring = make_small_ring([(10, "B", 0), (10, "A", 0), (40, "C", 0)])
        self.assertEqual(ring.get_owner(95), (10, "A", 0))


class TestAddRemove(unittest.TestCase):
    def test_add_node_creates_v_points(self):
        ring = HashRing(5)
        self.assertTrue(ring.add_node("A"))
        self.assertEqual(ring.node_count(), 1)
        self.assertEqual(ring.point_count(), 5)
        self.assertEqual(sorted(p[2] for p in ring.points), [0, 1, 2, 3, 4])
        for pos, node, j in ring.points:
            self.assertEqual(node, "A")
            self.assertEqual(pos, hash_to_position(f"node:A:{j}"))

    def test_points_stay_sorted(self):
        ring = HashRing(8)
        for name in "ABCDE":
            ring.add_node(name)
        self.assertEqual(ring.points, sorted(ring.points))
        self.assertEqual(ring.point_count(), 5 * 8)

    def test_add_duplicate_rejected(self):
        ring = HashRing(4)
        ring.add_node("A")
        before = list(ring.points)
        self.assertFalse(ring.add_node("A"))
        self.assertEqual(ring.points, before)
        self.assertEqual(ring.node_count(), 1)

    def test_remove_missing_rejected(self):
        ring = HashRing(4)
        ring.add_node("A")
        ring.add_node("B")
        before = list(ring.points)
        self.assertFalse(ring.remove_node("Z"))
        self.assertEqual(ring.points, before)

    def test_cannot_remove_last_node(self):
        ring = HashRing(4)
        ring.add_node("A")
        self.assertFalse(ring.remove_node("A"))
        self.assertEqual(ring.node_count(), 1)
        self.assertEqual(ring.point_count(), 4)

    def test_remove_keeps_other_points_unchanged(self):
        ring = HashRing(6)
        for name in "ABC":
            ring.add_node(name)
        keep = [p for p in ring.points if p[1] != "B"]
        self.assertTrue(ring.remove_node("B"))
        self.assertEqual(ring.points, keep)
        self.assertNotIn("B", ring.nodes)
        self.assertEqual(ring.point_count(), 2 * 6)

    def test_add_does_not_move_existing_points(self):
        ring = HashRing(6)
        ring.add_node("A")
        ring.add_node("B")
        old = set(ring.points)
        ring.add_node("C")
        self.assertTrue(old.issubset(set(ring.points)))

    def test_readd_after_remove_gives_same_points(self):
        ring = HashRing(6)
        for name in "ABC":
            ring.add_node(name)
        snapshot = list(ring.points)
        ring.remove_node("C")
        ring.add_node("C")
        self.assertEqual(ring.points, snapshot)  # แฮชคงที่ -> วงแหวนเหมือนเดิม


class TestRealRing(unittest.TestCase):
    def build(self, names, v=20):
        ring = HashRing(v)
        for name in names:
            ring.add_node(name)
        return ring

    def test_owner_of_guest_matches_position(self):
        ring = self.build("ABC")
        for c, s in [(1, 1), (2, 5), (30, 7)]:
            pos = hash_to_position(f"guest:{c}:{s}")
            self.assertEqual(ring.get_owner_of_guest(c, s), ring.get_owner(pos))

    def test_owner_is_always_a_live_node(self):
        ring = self.build("ABCD")
        for c in range(1, 40):
            for s in range(1, 40):
                self.assertIn(ring.get_owner_of_guest(c, s)[1], ring.nodes)

    def test_deterministic_across_instances(self):
        r1, r2 = self.build("ABC"), self.build("CBA")  # ลำดับเพิ่มต่างกัน ผลต้องเหมือนกัน
        self.assertEqual(r1.points, r2.points)
        for c in range(1, 30):
            self.assertEqual(r1.get_owner_of_guest(c, 1), r2.get_owner_of_guest(c, 1))

    def test_add_node_only_moves_guests_to_new_node(self):
        ring = self.build("ABC")
        guests = [(c, s) for c in range(1, 41) for s in range(1, 26)]
        before = {g: ring.get_owner_of_guest(*g)[1] for g in guests}
        ring.add_node("D")
        moved = 0
        for g in guests:
            after = ring.get_owner_of_guest(*g)[1]
            if after != before[g]:
                moved += 1
                self.assertEqual(after, "D")
        self.assertGreater(moved, 0)
        self.assertLess(moved, len(guests))

    def test_remove_node_only_moves_guests_of_removed_node(self):
        ring = self.build("ABCD")
        guests = [(c, s) for c in range(1, 41) for s in range(1, 26)]
        before = {g: ring.get_owner_of_guest(*g)[1] for g in guests}
        ring.remove_node("C")
        for g in guests:
            after = ring.get_owner_of_guest(*g)[1]
            if before[g] != "C":
                self.assertEqual(after, before[g])
            else:
                self.assertNotEqual(after, "C")

    def test_counts(self):
        ring = self.build("ABCDE", v=7)
        self.assertEqual(ring.node_count(), 5)
        self.assertEqual(ring.point_count(), 35)


if __name__ == "__main__":
    unittest.main()