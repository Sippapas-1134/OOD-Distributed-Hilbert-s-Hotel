"""
hashring.py
งานของ: คนที่ 1 -- วงแหวนและการเลือกอาคาร (Consistent Hashing Ring)

หน้าที่ที่ต้องทำ (ดูรายละเอียดกติกาในโจทย์ หัวข้อ 4.3 และ 4.4):
1. คลาส HashRing เก็บ "จุด" (virtual node) ของแต่ละอาคารบนวงแหวน 0 .. 2**64 - 1
2. แฮชต้องคงที่ข้ามการรันโปรแกรม -> ใช้ hashlib.sha256 เท่านั้น ห้ามใช้ hash() ของ Python
3. ข้อความที่นำไปแฮชต้องแยกรูปแบบชัดเจน:
     - แขก:   f"guest:{c}:{s}"
     - จุดอาคาร: f"node:{node_id}:{j}"   โดย j = 0..V-1
4. เก็บจุดแบบเรียงลำดับ (แนะนำ: list ของ tuple (position, node_id, j) + ใช้ bisect
   ตอนแทรก/ค้นหา เพื่อให้ค้นหาได้ O(log M))
5. หา "เจ้าของ" ตำแหน่งแขก = จุดแรกที่ position >= ตำแหน่งแขก
   ถ้าไม่มี (ตำแหน่งแขกมากกว่าทุกจุด) ให้วนกลับไปจุดแรกของวงแหวน (index 0)
6. ถ้าตำแหน่งชนกัน (position เท่ากันหลายจุด) ให้เรียงด้วยคีย์ (position, node_id, j)
   แล้วใช้จุดแรกตามลำดับนี้เป็นเจ้าของ
7. add_node(node_id) ต้องปฏิเสธถ้า node_id มีอยู่แล้ว (ห้ามใส่ virtual node ซ้ำ)
8. remove_node(node_id) ต้องปฏิเสธถ้า node_id ไม่มีอยู่จริง
   และห้ามลบอาคารสุดท้าย (ต้องมี N >= 1 อาคารเสมอ) -> คืนค่า/เหตุผลให้ hotel_system.py
   ไปแจ้งผู้ใช้ต่อ (อย่า raise exception ที่ทำให้โปรแกรมหยุด)

สิ่งที่ 'ห้าม' ทำ (ตามโจทย์):
- ห้ามใช้ไลบรารี consistent hashing สำเร็จรูป
- ห้ามใช้ hash() ของ Python เป็นแฮชหลัก
- ห้ามเปลี่ยนตำแหน่งของจุดที่ยังอยู่ตอนเพิ่ม/ลบอาคารอื่น
- ห้ามเปลี่ยนค่า V ระหว่างรอบเดียวกัน

ทดสอบที่ต้องเขียน (ใน tests/test_hashring.py):
- ใช้ตัวอย่างวงแหวนเล็กในโจทย์ หัวข้อ 9.1 (วงแหวนขนาด 100, V=1,
  A ที่ 20, B ที่ 50, C ที่ 80) มากำหนดตำแหน่งเอง (ไม่ต้องพึ่ง SHA-256 จริง)
  เพื่อตรวจตรรกะ get_owner() ให้ตรงตามตารางในโจทย์
- ทดสอบกรณีวนกลับต้นวงแหวน (ตำแหน่งแขก 90 -> ต้องได้อาคาร A)
- ทดสอบกรณีจุดชนกัน
"""

"""
ไม่แน่
                    worse       avg         expect
hash_to_position    O(1)        O(1)        O(1)
add_node            O(NV²)      O(NV²)      O(NV²)
remove_node         O(N + M)    O(M)        O(M)
get_owner           O(log M)    O(log M)    O(log M)
get_owner_of_guest  O(log M)    O(log M)    O(log M)
node_count          O(1)        O(1)        O(1)
point_count         O(1)        O(1)        O(1)
"""

import hashlib
from bisect import bisect_left, insort

RING_SIZE = 2 ** 64


def hash_to_position(key: str) -> int:  #O(1)
    """
    แปลงข้อความ (string) เป็นตำแหน่งบนวงแหวน 0 .. 2**64 - 1
    ใช้ SHA-256 แล้วตัดมา 64 บิตแรก (8 ไบต์แรก) ตามที่กติกากำหนด
    ต้องระบุวิธีการเข้ารหัสข้อความ (encoding) ในรายงานด้วย (ใช้ utf-8)

    ตัวอย่างการ implement (ปรับ/อธิบายในรายงานได้ตามที่กลุ่มออกแบบ):
        h = hashlib.sha256(key.encode("utf-8")).digest()
        return int.from_bytes(h[:8], byteorder="big")
    """

    h = hashlib.sha256(key.encode("utf-8")).digest()  #hash ด้วย SHA-256 แล้วแปลงเป็น bytes
    return int.from_bytes(h[:8], byteorder="big") #เอาแค่ 8 bytes แรก (64 bits) ของ hash มาแปลงเป็น int เรียงแบบ big-endian

class HashRing:

    def __init__(self, num_virtual_nodes_per_building: int):
        self.v = num_virtual_nodes_per_building
        self.points: list[tuple[int, str, int]] = []  #เก็บจุดทั้งหมด(len(self.points) == M) ประกอบด้วย position(key ที่ผ่านการ hash),node_id,j
        self.nodes: set[str] = set() #เก็บอาคาร(node_id) len(self.nodes) == N

    def add_node(self, node_id: str) -> bool:   #O(V) -> O(NV^2)
        """
        เพิ่มอาคาร node_id พร้อม virtual node ทั้ง V จุด
        คืนค่า True ถ้าเพิ่มสำเร็จ, False ถ้า node_id มีอยู่แล้ว (ปฏิเสธการเพิ่ม)
        ต้องแทรกจุดใหม่โดยรักษาลำดับของ self.points ไว้เสมอ (ใช้ insort หรือ bisect_left เอง)
        """

        if node_id not in self.nodes: #ตรวจสอบว่าเคยมี node_id นี้หรือไม่ 
            self.nodes.add(node_id)
        else:
            return False

        #add position node_id and j
        for j in range(self.v):     # O(v)
            position = hash_to_position(f"node:{node_id}:{j}")
            point = (position, node_id, j)
            insort(self.points,point) # O(M)

        return True

    def remove_node(self, node_id: str) -> bool: #O(N+M)
        """
        ลบอาคาร node_id พร้อม virtual node ทั้งหมดของอาคารนั้น
        คืนค่า True ถ้าลบสำเร็จ
        คืนค่า False ถ้า node_id ไม่มีอยู่จริง หรือถ้าลบแล้วจะไม่เหลืออาคารเลย (N >= 1)
        ห้ามเปลี่ยนตำแหน่งจุดของอาคารอื่นที่เหลืออยู่
        """

        if node_id in self.nodes and len(self.nodes)>1:
            self.nodes.remove(node_id)  #O(N)

            #ลบตัวที่มี node_id
            self.points = [i for i in self.points if i[1]!=node_id] #O(M)
            return True
        else:
            return False

    def get_owner(self, position: int) -> str | None: #O(log M)
        """
        หา node_id ที่เป็นเจ้าของตำแหน่ง position
        กติกา: จุดแรกที่ position(จุด) >= position(แขก) ถ้าไม่มีให้วนกลับจุดแรกของวงแหวน (index 0)
        คืนค่า None ถ้าวงแหวนว่าง (ไม่ควรเกิดขึ้นถ้ารักษา N >= 1 ไว้เสมอ)
        แนะนำใช้ bisect_left บน list ของ position ล้วน ๆ (แยกเก็บหรือ derive ทุกครั้งก็ได้
        แต่ให้คำนึงถึง Big-O ตามที่จะวิเคราะห์ในรายงาน)
        """

        if self.node_count == 0:
            return None

        #หา position ของจุดที่ >= position ของ gusest
        index = bisect_left(self.points,(position,0,0)) # O(log M)

        if index == self.point_count:
            return self.points[0]
        
        return self.points[index]

    def get_owner_of_guest(self, c: int, s: int) -> str | None: #O(log M)
        """
        คำนวณตำแหน่งของแขกจาก (c, s) ด้วย hash_to_position("guest:c:s")
        แล้วเรียก get_owner() ต่อ
        """

        position = hash_to_position(f"guest:{c}:{s}")   #O(1)
        return self.get_owner(position) #O(log M)

    # จำนวนอาคาร N
    def node_count(self) -> int:
        return len(self.nodes)

    #จำนวนจุด M = N x V
    def point_count(self) -> int:
        """จำนวนจุดทั้งหมดบนวงแหวน = M = N * V"""

        return len(self.points)
