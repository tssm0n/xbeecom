import thread, serial

class XbeeCom:
    # Message structure - (source, destination, data)
    # Custom raw packet format (for transparent mode):
    # (125, 126, source, destination, numbermsb, numberlsb, length, 1-n data bytes, checksum)
    def __init__(self, api = False):
        self.api = api
        self.raw_buffer = []
        self.packet_buffer = []
        self.number = 0
        self.pb_lock = thread.allocate_lock()
    def data_available(self):
        return len(self.packet_buffer) > 0
    def next_packet(self):
        self.pb_lock.acquire()
        result = self.packet_buffer[0]
        self.packet_buffer = self.packet_buffer[1:]
        self.pb_lock.release()
        return result
    def send_packet(self, packet):
        if self.api:
            data = self._prepare_api_packet(packet)
        else:
            data = self._prepare_packet(packet)
        self.send_raw(data)
    def _prepare_packet(self, packet):
        data = [125, 126, packet[0], packet[1]]
        self._append_id(data)
        data.append(len(packet[2]))
        data.extend(packet[2])
        data.append(self._checksum(packet[2]))
        return data
    def _receive_packet(self, raw):
        if raw[0] != 125 or raw[1] != 126:
            print "Incorrect header"
            return None
        data = raw[7:-1]
        if raw[-1] != self._checksum(data):
            print "Incorrect checksum"
            return None
        return (raw[2], raw[3], data)
    def _prepare_api_packet(self, packet, command = 1):
        data = [0x7E, 0, 0]
        checksumable = [command, 0, packet[1]] #Note, doesn't handle destination IDs > 255
        checksumable.extend(packet[2])
        data.extend(checksumable)
        data.append(self._checksum(checksumable))
        data[2] = len(checksumable) # Note, doesn't handle more than 255 bytes
        return data
    def _checksum(self, data):
        total = 0
        for d in data:
            total += d
        return 0xFF - (total % 0xFF)
    def _append_id(self, data):
        result = [0, 0]
        num = self._next_id()
        bVal = toBytes(num)
        index = 0
        if len(bVal) > 0:
            if len(bVal) >= 2:
                result[0] = bVal[0]
                index += 1
            result[1] = bVal[index]
        data.extend(result)
    def _next_id(self):
        result = self.number
        self.number += 1
        if self.number > 65535:
            self._reset_id
        return result
    def _reset_id(self):
        self.number = 0
    def _is_packet_complete(self):
        if len(self.raw_buffer) == 0:
            return False
        if len(self.raw_buffer) == 1:
            if self.raw_buffer[0] != 125:
                print "Invalid buffer, resetting. Found0: " + self.raw_buffer[0]
                self.raw_buffer = []
            return False
        if len(self.raw_buffer) == 2:
            if self.raw_buffer[1] != 126:
                print "Invalid buffer, resetting. Found1: " + self.raw_buffer[1]
                self.raw_buffer = []
            return False
        if len(self.raw_buffer) < 8:
           return False
        expected = self.raw_buffer[6] + 8
        if len(self.raw_buffer) == expected:
           return True
        return False            
    def _receive_byte(self, byte):
        val = byte
        if type(val) is str:
            val = ord(val)
        self.raw_buffer.append(val)
        if self._is_packet_complete():
            self.pb_lock.acquire()
            self.packet_buffer.append(self._receive_packet(self.raw_buffer))
            self.raw_buffer = []
            self.pb_lock.release()

class XbeeController:
    def __init__(self, com, sourceId = 0):
        self.com = com
        self.id = sourceId
    def _send(self, destination, raw_data):
        self.com.send_packet((self.id, destination, raw_data))
    def _receive(self):
        if self.com.data_available():
            return self.com.next_packet()
        return None
    
class DummyCom(XbeeCom):
    def __init__(self, pair = None):
        XbeeCom.__init__(self)
        if pair == None:
            self.pair = DummyCom(self)
        else:
            self.pair = pair
    def send_raw(self, data):
        for d in data:
            self.pair._receive_byte(d)

class DummyController(XbeeController):
    def __init__(self, com, sourceId):
        XbeeController.__init__(self, com, sourceId)
        thread.start_new_thread(self.monitor, ())
        self.done = False
    def monitor(self):
        while not self.done:
            data = self._receive()
            if data != None:
                print data

class SerialCom(XbeeCom):
    def __init__(self, port, baud = 9600):
        XbeeCom.__init__(self)
        self.serial = serial.Serial(port, baud, timeout = 0.01)
        self.done = False
        thread.start_new_thread(self.monitor, ())
    def monitor(self):
        while not self.done:
            input = self.serial.read(1)
            self._process_input(input)
        self.serial.close()
    def exit(self):
        self.done = True
        print "Exiting"
    def send_raw(self, data):
        byteObj = bytearray(data)
        self.serial.write(byteObj)
    def _process_input(self, input):
        if len(input) > 0:
            for i in input:
                val = i
                if type(val) is str:
                    val = ord(val)
                self._receive_byte(val)

# Some utility funcions
def toBytes(val):
    result = []
    while val:
        result.append(val&0xFF)
        val >>= 8
    return result


