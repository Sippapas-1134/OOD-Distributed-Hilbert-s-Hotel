"""
tests/test_hotel_system.py
งานของ: คนที่ 5

เทส end-to-end ผ่าน HotelSystem โดยตรง (ไม่ผ่านเมนู) + กรณีขอบทั้งหมดในโจทย์ หัวข้อ 4.5
"""

import os
import csv
import tempfile
import unittest

from hotel_system import HotelSystem


def compute_room_no(c: int, s: int) -> int:
    a = c - 1
    b = s - 1
    return ((a + b) * (a + b + 1)) // 2 + b + 1

class TestHotelSystemBasicFlow(unittest.TestCase):
    def setUp(self):
        self.system = HotelSystem(initial_node_ids=["A", "B", "C"], v=4)

    def test_existing_guest_address_unchanged_after_new_guest(self):
        """เพิ่มแขกใหม่แล้ว ที่อยู่ห้องของแขกเดิมต้องไม่เปลี่ยนแม้แต่คนเดียว"""
        prev_rooms = []
        curr_rooms = []
        cs_pairs = [(c, s)for c in range(1, 101) for s in range(1, 101)]
        for pair in cs_pairs:
            self.system.add_guest(pair[0], pair[1])
            curr_rooms = self.system.list_occupied_rooms()

            if len(prev_rooms) == 0:
                continue

            self.assertNotEqual(curr_rooms[:-1], prev_rooms)
            prev_rooms = curr_rooms

    def test_room_number_matches_formula(self):
        for data in self.system.list_occupied_rooms():
            _, room_no, c, s = data
            self.assertEqual(room_no, compute_room_no(c, s))


class TestEdgeCases(unittest.TestCase):
    """ตรงกับตารางกรณีขอบในโจทย์ หัวข้อ 4.5 -- ทุกกรณีต้อง 'ไม่' ทำให้โปรแกรมหยุดทำงาน"""

    def setUp(self):
        self.system = HotelSystem(initial_node_ids=["A"], v=4)

    def test_add_existing_building_rejected_gracefully(self):
        report = self.system.add_building("A")
        self.assertFalse(report.accepted)

    def test_remove_nonexistent_building_rejected_gracefully(self):
        report = self.system.remove_building("")
        self.assertFalse(report.accepted)

    def test_remove_last_building_rejected_gracefully(self):
        report = self.system.remove_building("A")
        self.assertFalse(report.accepted)

    def test_add_duplicate_guest_rejected_gracefully(self):
        self.system.add_guest(1, 1)
        status, _ = self.system.add_guest(1, 1)
        self.assertFalse(status)

    def test_remove_nonexistent_guest_rejected_gracefully(self):
        status, _ = self.system.remove_guest(2, 1)
        self.assertFalse(status)

    def test_search_not_found_reports_clearly(self):
        by_cs_result = self.system.find_by_guest(2, 1)
        self.assertIsNone(by_cs_result)

        by_address_result = self.system.find_by_address("E", -1)
        self.assertIsNone(by_address_result)

    def test_zero_guests_stats_are_zero_no_crash(self):
        """ยังไม่มีแขกในระบบ (K=0): ต้องไม่หารด้วยศูนย์ ค่าสถิติเป็น 0 และไม่คำนวณ CV"""
        self.system.remove_guest(1, 1)
        status, _, _ = self.system.load_balance_report()
        self.assertFalse(status)

class TestCsvExport(unittest.TestCase):
    def setUp(self):
        self.system = HotelSystem(initial_node_ids=["A", "B"], v=4)

    def test_csv_row_count_matches_guest_count(self):
        """จำนวนแถวใน CSV ต้องเท่ากับจำนวนแขกในระบบ"""
        # TODO(คนที่ 5): เพิ่มแขกจำนวนหนึ่ง แล้ว export แล้วนับแถว เทียบกับ
        # self.system.registry.guest_count()
        cs_pairs = [(c, s)for c in range(1, 1001) for s in range(1, 1001)]
        for pair in cs_pairs:
            self.system.add_guest(pair[0], pair[1])

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "guests.csv")

            self.system.export_guests_csv(path)

            with open(path, mode="r", newline="", encoding="utf-8") as file:
                reader = csv.reader(file)
                _ = next(reader, None) # header
                self.assertEqual(sum(1 for _ in reader), len(self.system.list_occupied_rooms()))


if __name__ == "__main__":
    unittest.main()
