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


class TestHotelSystemBasicFlow(unittest.TestCase):
    def setUp(self):
        self.system = HotelSystem(initial_node_ids=["A", "B", "C"], v=4)

    def test_existing_guest_address_unchanged_after_new_guest(self):
        """เพิ่มแขกใหม่แล้ว ที่อยู่ห้องของแขกเดิมต้องไม่เปลี่ยนแม้แต่คนเดียว"""
        pass

    def test_room_number_matches_formula(self):
        pass


class TestEdgeCases(unittest.TestCase):
    """ตรงกับตารางกรณีขอบในโจทย์ หัวข้อ 4.5 -- ทุกกรณีต้อง 'ไม่' ทำให้โปรแกรมหยุดทำงาน"""

    def setUp(self):
        self.system = HotelSystem(initial_node_ids=["A"], v=4)

    def test_add_existing_building_rejected_gracefully(self):
        pass

    def test_remove_nonexistent_building_rejected_gracefully(self):
        pass

    def test_remove_last_building_rejected_gracefully(self):
        pass

    def test_add_duplicate_guest_rejected_gracefully(self):
        pass

    def test_remove_nonexistent_guest_rejected_gracefully(self):
        pass

    def test_search_not_found_reports_clearly(self):
        pass

    def test_zero_guests_stats_are_zero_no_crash(self):
        """ยังไม่มีแขกในระบบ (K=0): ต้องไม่หารด้วยศูนย์ ค่าสถิติเป็น 0 และไม่คำนวณ CV"""
        pass


class TestCsvExport(unittest.TestCase):
    def setUp(self):
        self.system = HotelSystem(initial_node_ids=["A", "B"], v=4)

    def test_csv_row_count_matches_guest_count(self):
        """จำนวนแถวใน CSV ต้องเท่ากับจำนวนแขกในระบบ"""
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "guests.csv")
            # TODO(คนที่ 5): เพิ่มแขกจำนวนหนึ่ง แล้ว export แล้วนับแถว เทียบกับ
            # self.system.registry.guest_count()
            pass


if __name__ == "__main__":
    unittest.main()
