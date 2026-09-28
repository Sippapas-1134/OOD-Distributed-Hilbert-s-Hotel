"""
tests/test_hashring.py
งานของ: คนที่ 1

ใช้ตัวอย่างวงแหวนเล็กในโจทย์ หัวข้อ 9.1 มาตรวจตรรกะ get_owner()
วงแหวนขนาด 100, V = 1 (กำหนดตำแหน่งเองในเทส ไม่ต้องพึ่งค่า SHA-256 จริง)
อาคาร A ที่ตำแหน่ง 20, B ที่ 50, C ที่ 80

หมายเหตุ: การ "กำหนดตำแหน่งเอง" หมายถึงอาจต้อง monkeypatch หรือเพิ่มเมธอด
เสริมใน HashRing สำหรับทดสอบ (เช่น insert จุดด้วยตำแหน่งที่กำหนดตรง ๆ
โดยไม่ผ่าน hash_to_position) -- ให้คนที่ 1 ออกแบบเพิ่มเติมเอง เพราะไฟล์ hashring.py
ปัจจุบันออกแบบให้ตำแหน่งมาจาก hash_to_position() เท่านั้น
"""

import unittest

from hashring import HashRing, hash_to_position


class TestHashToPosition(unittest.TestCase):
    def test_deterministic(self):
        """แฮชค่าเดียวกันต้องได้ตำแหน่งเดียวกันทุกครั้ง (คงที่ข้ามการรัน)"""
        # TODO(คนที่ 1): เติม assert เมื่อ hash_to_position implement เสร็จ
        pass

    def test_different_keys_different_positions_usually(self):
        """ข้อความต่างกันควรได้ตำแหน่งต่างกัน (ไม่ใช่การพิสูจน์ทางคณิตศาสตร์ แต่เป็น sanity check)"""
        pass


class TestHashRingBasic(unittest.TestCase):
    def setUp(self):
        self.ring = HashRing(num_virtual_nodes_per_building=1)

    def test_add_node_rejects_duplicate(self):
        """เพิ่มอาคารซ้ำต้องถูกปฏิเสธ (return False) ไม่ throw exception"""
        pass

    def test_remove_node_rejects_unknown(self):
        """ลบอาคารที่ไม่มีอยู่ต้อง return False ไม่ throw exception"""
        pass

    def test_remove_last_node_rejected(self):
        """ลบอาคารสุดท้ายที่เหลืออยู่ต้องถูกปฏิเสธ (N >= 1 เสมอ)"""
        pass


class TestGetOwnerExampleFromSpec(unittest.TestCase):
    """
    ตัวอย่างวงแหวนเล็กจากโจทย์ หัวข้อ 9.1:
    A=20, B=50, C=80 (วงแหวนขนาด 100)
    ตารางคาดหวัง (สถานะเริ่มต้น A,B,C):
      ตำแหน่งแขก 10 -> A
      ตำแหน่งแขก 20 -> A
      ตำแหน่งแขก 25 -> B
      ตำแหน่งแขก 35 -> B
      ตำแหน่งแขก 50 -> B
      ตำแหน่งแขก 70 -> C
      ตำแหน่งแขก 90 -> A   (วนกลับต้นวงแหวน)

    เพิ่ม D ที่ 35:
      ตำแหน่งแขก 25 -> D (ย้ายจาก B)
      ตำแหน่งแขก 35 -> D (ย้ายจาก B)
      (คนอื่นไม่เปลี่ยน) รวมย้าย 2 คน

    ลบ B จากสถานะเริ่มต้น (A,B,C):
      ตำแหน่งแขก 25 -> C (ย้ายจาก B)
      ตำแหน่งแขก 35 -> C (ย้ายจาก B)
      ตำแหน่งแขก 50 -> C (ย้ายจาก B)
      รวมย้าย 3 คน
    """

    def test_initial_assignment(self):
        # TODO(คนที่ 1): ต้องหาวิธีแทรกจุดที่ตำแหน่งกำหนดตรง ๆ (20,50,80) แล้วตรวจ get_owner()
        pass

    def test_add_d_migrates_two_guests_only(self):
        pass

    def test_remove_b_migrates_three_guests_only(self):
        pass


if __name__ == "__main__":
    unittest.main()
