"""
tests/test_rebalance.py
งานของ: คนที่ 3

ใช้ตัวอย่างวงแหวนเล็กจากโจทย์ หัวข้อ 9.1 (เหมือน test_hashring.py) มาตรวจ
add_building / remove_building แบบครบวงจร (ring + registry ทำงานร่วมกัน)
"""

import unittest

from hashring import HashRing
from guest import GuestRegistry
import rebalance


class TestRebalanceWithSpecExample(unittest.TestCase):
    def setUp(self):
        # TODO(คนที่ 3): ตั้งค่าวงแหวน A=20,B=50,C=80 ตามตัวอย่างในโจทย์
        # และเพิ่มแขก 7 คนตามตารางในหัวข้อ 9.1 ก่อนแต่ละเทส
        pass

    def test_add_building_migrates_only_two(self):
        """เพิ่ม D ที่ตำแหน่ง 35 ต้องมีคนย้ายเข้า D เท่านั้น 2 คน คนอื่นไม่ขยับ"""
        pass

    def test_remove_building_migrates_only_three(self):
        """ลบ B จากสถานะเริ่มต้น ต้องมีคนย้าย 3 คน (เฉพาะที่เคยอยู่ B) อาคารอื่นไม่ขยับ"""
        pass

    def test_room_no_unchanged_after_migration(self):
        """room_no ของทุกคนที่ย้ายต้องเท่าเดิม เปลี่ยนแค่ node_id"""
        pass

    def test_guest_count_invariant(self):
        """จำนวนแขกรวมในระบบต้องไม่เพิ่มไม่ลดหลังเพิ่ม/ลบอาคาร"""
        pass


class TestRebalanceEdgeCases(unittest.TestCase):
    def test_add_building_duplicate_rejected(self):
        pass

    def test_remove_building_unknown_rejected(self):
        pass

    def test_remove_last_building_rejected(self):
        pass

    def test_zero_guests_move_rate_reported_as_none_or_zero(self):
        """K = 0: รายงานจำนวนย้ายเป็น 0 และไม่คำนวณอัตรา (move_rate ควรเป็น None)"""
        pass


if __name__ == "__main__":
    unittest.main()
