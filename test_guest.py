import random
import unittest

from guest import GuestRegistry, compute_room_no


class TestRoomNo(unittest.TestCase):
    def test_sample_table(self):
        for (c, s), expected in {(1, 1): 1, (2, 1): 2, (1, 2): 3, (3, 1): 4, (2, 2): 5}.items():
            self.assertEqual(compute_room_no(c, s), expected)

    def test_no_collision_random(self):
        rng = random.Random(42)
        seen = {}
        for _ in range(50000):
            code = (rng.randint(1, 3000), rng.randint(1, 3000))
            room = compute_room_no(*code)
            if room in seen:
                self.assertEqual(seen[room], code)
            seen[room] = code

    def test_no_collision_exhaustive_small(self):
        rooms = [compute_room_no(c, s) for c in range(1, 101) for s in range(1, 101)]
        self.assertEqual(len(rooms), len(set(rooms)))

    def test_big_ints_exact(self):
        c, s = 10**30, 10**30
        a, b = c - 1, s - 1
        self.assertEqual(compute_room_no(c, s), ((a + b) * (a + b + 1)) // 2 + b + 1)

    def test_invalid(self):
        for bad in [(0, 1), (1, 0), (-1, 5)]:
            with self.assertRaises(ValueError):
                compute_room_no(*bad)


class TestRegistry(unittest.TestCase):
    def setUp(self):
        self.r = GuestRegistry()

    def test_add_and_find(self):
        self.assertEqual(self.r.add_guest(2, 2, "A"), (True, ""))
        self.assertEqual(self.r.find_by_guest_code(2, 2), ("A", 5))
        self.assertEqual(self.r.find_by_address("A", 5), (2, 2))
        self.assertIsNone(self.r.find_by_guest_code(9, 9))
        self.assertIsNone(self.r.find_by_address("A", 99))

    def test_reject_duplicate_single(self):
        self.r.add_guest(1, 1, "A")
        ok, reason = self.r.add_guest(1, 1, "B")
        self.assertFalse(ok)
        self.assertTrue(reason)
        self.assertEqual(self.r.find_by_guest_code(1, 1), ("A", 1))
        self.assertEqual(self.r.guest_count(), 1)

    def test_batch_ok(self):
        ok, _, added = self.r.add_guests_batch(1, 1, 5, lambda c, s: "A")
        self.assertTrue(ok)
        self.assertEqual(added, [(1, s) for s in range(1, 6)])
        self.assertEqual(self.r.guest_count(), 5)

    def test_batch_zero(self):
        self.assertEqual(
            self.r.add_guests_batch(1, 1, 0, lambda c, s: "A"),
            (True, "ไม่มีการเปลี่ยนแปลง", []),
        )
        self.assertEqual(self.r.guest_count(), 0)

    def test_batch_negative_count(self):
        ok, _, added = self.r.add_guests_batch(1, 1, -1, lambda c, s: "A")
        self.assertFalse(ok)
        self.assertEqual(added, [])

    def test_batch_rejects_whole_group_on_one_dup(self):
        self.r.add_guest(1, 3, "X")
        before = dict(self.r.by_guest_code), dict(self.r.by_address)
        ok, _, added = self.r.add_guests_batch(1, 1, 5, lambda c, s: "A")
        self.assertFalse(ok)
        self.assertEqual(added, [])
        self.assertEqual((self.r.by_guest_code, self.r.by_address), before)

    def test_batch_lookup_failure_leaves_no_partial(self):
        def bad(c, s):
            if s == 3:
                raise RuntimeError("ring ว่าง")
            return "A"

        ok, _, _ = self.r.add_guests_batch(1, 1, 5, bad)
        self.assertFalse(ok)
        self.assertEqual(self.r.guest_count(), 0)
        self.assertEqual(len(self.r.by_address), 0)

    def test_remove(self):
        self.r.add_guest(1, 1, "A")
        self.assertEqual(self.r.remove_guest(1, 1), (True, ""))
        self.assertIsNone(self.r.find_by_guest_code(1, 1))
        self.assertIsNone(self.r.find_by_address("A", 1))
        self.assertEqual(len(self.r.by_address), 0)

    def test_remove_missing_no_exception(self):
        ok, reason = self.r.remove_guest(7, 7)
        self.assertFalse(ok)
        self.assertTrue(reason)

    def test_readd_after_remove(self):
        self.r.add_guest(1, 1, "A")
        self.r.remove_guest(1, 1)
        self.assertEqual(self.r.add_guest(1, 1, "B"), (True, ""))
        self.assertEqual(self.r.find_by_guest_code(1, 1), ("B", 1))

    def test_update_node(self):
        self.r.add_guest(2, 2, "A")
        self.r.update_node_of_guest(2, 2, "B")
        self.assertEqual(self.r.find_by_guest_code(2, 2), ("B", 5))
        self.assertIsNone(self.r.find_by_address("A", 5))
        self.assertEqual(self.r.find_by_address("B", 5), (2, 2))
        self.assertEqual(len(self.r.by_address), 1)

    def test_update_node_same_node(self):
        self.r.add_guest(1, 1, "A")
        self.r.update_node_of_guest(1, 1, "A")
        self.assertEqual(self.r.find_by_address("A", 1), (1, 1))

    def test_list_sorted(self):
        self.r.add_guest(3, 1, "A")  # 4
        self.r.add_guest(1, 1, "A")  # 1
        self.r.add_guest(2, 2, "A")  # 5
        self.r.add_guest(2, 1, "B")  # 2
        self.assertEqual(
            self.r.list_guests_in_building("A"), [(1, 1, 1), (4, 3, 1), (5, 2, 2)]
        )
        self.assertEqual(self.r.list_guests_in_building("Z"), [])

    def test_indexes_consistent(self):
        rng = random.Random(1)
        for _ in range(500):
            c, s = rng.randint(1, 20), rng.randint(1, 20)
            op = rng.choice(["add", "remove", "move"])
            if op == "add":
                self.r.add_guest(c, s, rng.choice("ABC"))
            elif op == "remove":
                self.r.remove_guest(c, s)
            elif (c, s) in self.r.by_guest_code:
                self.r.update_node_of_guest(c, s, rng.choice("ABC"))
        self.assertEqual(len(self.r.by_guest_code), len(self.r.by_address))
        for (c, s), rec in self.r.by_guest_code.items():
            self.assertEqual(self.r.by_address[(rec.node_id, rec.room_no)], (c, s))


if __name__ == "__main__":
    unittest.main()