import unittest
from xbee import *

class XbeeComTest(unittest.TestCase):
    def setUp(self):
        self.com = XbeeCom()

    def test_data_available(self):
        self.assertFalse(self.com.data_available())

    def test_prepare_packet(self):
        self.com.number = 100
        actual = self.com._prepare_packet((1, 2, [3, 4]))
        self.assertEqual(actual, [125, 126, 1, 2, 0, 100, 2, 3, 4, 248])

    def test_prepare_api_packet(self):
        actual = self.com._prepare_api_packet((1, 2, [3, 4]))
        self.assertEqual(actual, [126, 0, 5, 1, 0, 2, 3, 4, 245])

    def test_receive_packet(self):
        data = self.com._prepare_packet((1, 2, [3, 4, 5, 6]))
        actual = self.com._receive_packet(data)
        self.assertEqual((1, 2, [3, 4, 5, 6]), actual)

    def test_receive_packet_bad(self):
        actual = self.com._receive_packet((125, 126, 0, 0, 1, 2, 0))
        self.assertTrue(actual == None)

    def test_checksum(self):
        data = [0x08, 0x52, 0x44, 0x4C]
        self.assertEqual(0x15, self.com._checksum(data))

    def test_receive_byte(self):
        packet = self.com._prepare_packet((1, 2, [3, 4]))
        for p in packet:
            self.com._receive_byte(p)
            if p != packet[-1]:
                self.assertFalse(self.com.data_available())
        self.assertTrue(self.com.data_available())

        packet2 = self.com._prepare_packet((1, 2, [3, 5]))
        for p in packet2:
            self.com._receive_byte(p)
            
        actual = self.com.next_packet()
        self.assertEquals((1, 2, [3, 4]), actual)
        actual = self.com.next_packet()
        self.assertEquals((1, 2, [3, 5]), actual)

    def test_toBytes(self):
        actual1 = toBytes(100)
        actual2 = toBytes(257)
        self.assertEquals(1, len(actual1))
        self.assertEquals(100, actual1[0])
        self.assertEquals(2, len(actual2))
        self.assertEquals(1, actual2[0])
        self.assertEquals(1, actual2[1])

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(XbeeComTest)
    unittest.TextTestRunner(verbosity=2).run(suite) 
