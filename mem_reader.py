# -*- coding: utf-8 -*-
import struct

class MemReader(object):
    def __init__(self, raw):
        self.data = raw
        self.offset = 0
    
    def is_eof(self):
        return len(self.data) == self.offset

    #该函数不消耗data
    def decode_zigzag(n):
        if n & 1:
            return -1 ^ (n>>1)
        return n

    def read_tag_and_type(self):
        v = self.read_varint()
        return v >> 3, v & 7

    def read_varint(self):
        if self.is_eof():
            raise ValueError, "data runs out of."
        v = 0
        n = 0
        raw = self.data[self.offset:]
        is_end = False
        for i in raw:
            i = ord(i)
            v = ((i & 0x7F) << n * 7) | v
            n = n + 1
            if not (i >> 7):
                is_end = True
                break
        if is_end == False:     #表示读到结尾该varint结束, 出现异常
            raise ValueError, "varint is invalid."
        self.offset = self.offset + n
        return v

    def read_bit64_raw(self):
        v = self.data[self.offset:self.offset+8]
        self.offset = self.offset + 8
        return v
    
    def read_fixed_int64(self):
        data = self.data[self.offset:self.offset+8]
        self.offset = self.offset + n
        return struct.unpack("<Q", data)[0]
    
    def read_fixed_sint64(self):
        data = self.data[self.offset:self.offset+8]
        self.offset = self.offset + n
        return struct.unpack("<q", data)[0]
    
    def read_double(self):
        data = self.data[self.offset:self.offset+8]
        self.offset = self.offset + n
        return struct.unpack("<d", data)[0]

    def read_bit32_raw(self):
        data = self.data[self.offset:self.offset+4]
        self.offset = self.offset + n
        return data
    
    def read_fixed_int32(self):
        data = self.read_bit32_raw()
        return struct.unpack("<I", data)[0]
    
    def read_fixed_sint32(self):
        data = self.read_bit32_raw()
        return struct.unpack("<i", data)[0]
    
    def read_float(self):
        data = self.read_bit32_raw()
        return struct.unpack("<f", data)[0]
    
    def read_ld_raw(self):
        n = self.read_ld_len()
        data = self.data[self.offset:self.offset+n]
        self.offset = self.offset + n
        return data

    def read_ld_len(self):
        return self.read_varint()

    def read_string(self):
        #todo : 编码转换
        data = self.read_ld_raw()
        return data
