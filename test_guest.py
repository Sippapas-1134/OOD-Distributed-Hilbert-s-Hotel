"""
tests/test_guest.py
งานของ: คนที่ 2
"""

import unittest

from guest import compute_room_no, GuestRegistry


class TestComputeRoomNo(unittest.TestCase):
    def test_spec_table(self):
        """ตรงกับตารางตัวอย่างในโจทย์ หัวข้อ 4.2"""
        expected = {
            (1, 1): 1,
            (2, 1): 2,
            (1, 2): 3,
            (3, 1): 4,
            (2, 2): 5,
        }
        for (c, s), room in expected.items():
            with self.subTest(c=c, s=s):
                self.assertEqual(compute_room_no(c, s), room)

    def test_no_duplicate_room_numbers(self):
        """สุ่มรหัสแขกจำนวนมาก แล้วตรวจว่า room_no ไม่ซ้ำกันเลย"""
        seen = {}
        for c in range(1, 50):
            for s in range(1, 50):
                room = compute_room_no(c, s)
                self.assertNotIn(room, seen, f"room_no ซ้ำ: {(c,s)} กับ {seen.get(room)}")
                seen[room] = (c, s)


class TestGuestRegistry(unittest.TestCase):
    def setUp(self):
        self.registry = GuestRegistry()

    def test_add_guest_success(self):
        pass

    def test_add_guest_rejects_duplicate(self):
        pass

    def test_add_guests_batch_rejects_whole_batch_on_any_duplicate(self):
        """ถ้ามีรหัสซ้ำแม้เพียงรายการเดียวในกลุ่ม ต้องปฏิเสธทั้งกลุ่ม และข้อมูลเดิมต้องไม่เปลี่ยน"""
        pass

    def test_remove_guest_not_found_does_not_crash(self):
        pass

    def test_find_by_guest_code_and_by_address_consistent(self):
        pass

    def test_update_node_of_guest_keeps_room_no(self):
        """เมื่อย้ายอาคาร room_no ต้องคงเดิม เปลี่ยนแค่ node_id"""
        pass


if __name__ == "__main__":
    unittest.main()
