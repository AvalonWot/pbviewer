# -*- coding: utf-8 -*-
from database_pb2 import *
import db
from mem_reader import *

main_type_set = set([MT_UNKNOW, VARINT, BIT64, LENGTH_DELIMI, BIT32])
varint_type_set = set([INT32, INT64, UINT32, UINT64, SINT32, SINT64, BOOL, ENUM])
bit64_type_set = set([FIXED64, SFIXED64, DOUBLE])
ld_type_set = set([STRING, BYTES, EMBEDDED_MESSAGES, PACKED_REPEATED_FIELDS])
bit32_set = set([FIXED32, SFIXED32, FLOAT])

#当修改过field或是message时, 请调用该函数, 这样可以让数据库知道是否出现过更新
_modified = False
def modified():
    _modified = True

class PBNode(object):
    _message = None
    _field = None
    _value = None

    def __init__(self, role):
        if type(role) == pb_message:
            self._message = role
            self._value = []
        elif type(role) == pb_field:
            self._field = role
            if self._field.prefix == REPEATED or self._field.subType == PACKED_REPEATED_FIELDS:
                self._value = []
        else:
            raise ValueError, "PBNode init need a pb_message or pb_field"

    def is_left(self):
        return self._message == None

    def is_newtag(self, tag):
        if self.is_left():
            raise ValueError, "left node can not use is_newtag()"
        return tag not in self._message.tags

    def search_sub_node(self, tag):
        if self.is_left():
            raise ValueError, "left PBNode can not use search_sub_node()"
        for node in self._value:
            if node._field == None:
                continue
            if node._field.tag == tag:
                return node
        return None

    def search_fields_in_message(self, tag):
        if self.is_left():
            raise ValueError, "left PBNode can not use search_fields_with_tag()"
        for field in self._message.fields:
            if field.tag == tag:
                return field
        return None

    #todu : check the input value's type
    def set_value(self, v):
        if not self.is_left():
            raise ValueError, "noleft PBNode can not use set_value()"
        if self._field.prefix == REPEATED or self._field.subType == PACKED_REPEATED_FIELDS:
            self._value.append(v)
        if self._value != None:
            l = []
            l.append(self._value)
            l.append(v)
            self._value = l
            self._field.prefix = REPEATED
            modified()
        else:
            self._value = v

    def set_field_main_type(self, mtype):
        if not self.is_left():
            raise ValueError, "noleft PBNode can not use set_field_main_type()"
        if self._field.mainType != mtype:
            self._field.mainType = mtype
            modified()

    def create_field_in_message(self, tag):
        if self.is_left():
            raise ValueError, "left PBNode can not use create_field_in_message()"
        self._message.tags.append(tag)
        field = self._message.fields.add()
        field.tag = tag
        modified()
        return field

    def create_sub_node(self, tag):
        if self.is_left():
            raise ValueError, "left PBNode can not create sub node"
        if self.search_sub_node(tag):
            #本意是在创建, 因此这里抛出异常
            raise ValueError, "tag instance already existed."
        field = None
        if self.is_newtag(tag):
            field = self.create_field_in_message(tag)
        else:
            field = self.search_fields_in_message(tag)
        assert(field)
        node = PBNode(field)
        self._value.append(node)
        return node

    #stype这样写感觉不协调, 但为了兼容PACKED_REPEATED_FIELDS
    def read_varint(self, reader, stype):
        #不在这里校验数值有效性
        v = reader.read_varint()
        if stype == SINT32 or stype == SINT64:
            v = reader.decode_zigzag(v)
        self.set_value(v)

    def read_bit64(self, reader, stype):
        if stype == FIXED64:
            v = reader.read_fixed_int64()
        elif stype == SFIXED64:
            v = reader.read_fixed_sint64()
        elif stype == DOUBLE:
            v = reader.read_double()
        else:
            v = reader.read_bit64_raw()
        self.set_value(v)

    def read_bit32(self, reader, stype):
        if stype == FIXED32:
            v = reader.read_fixed_int32()
        elif stype == SFIXED32:
            v = reader.read_fixed_sint32()
        elif stype == FLOAT:
            v = reader.read_float()
        else:
            v = reader.read_bit32_raw()
        self.set_value(v)

    #这个函数与之前的read_系列不同, 设计不好, 不能递归
    def read_ld(self, reader, stype):
        if stype == STRING:
            v = reader.read_string()
        elif stype == BYTES:
            v = reader.read_ld_raw()
        elif stype == EMBEDDED_MESSAGES:
            #这个比较关键
            data = reader.read_ld_raw()
            msg = db.get_message(self._field.message_id)
            if msg == None:
                msg = db.create_message()
            v = PBNode(msg)
            v.read_from_string(data)
        elif stype == PACKED_REPEATED_FIELDS:
            if self._field.HasField('repeated_type'):
                n = reader.read_ld_len()
                if self._field.repeated_type in varint_type_set:
                    func = self.read_varint
                elif self._field.repeated_type in bit32_set:
                    func = self.read_bit32
                elif self._field.repeated_type in bit64_type_set:
                    func = self.read_bit64
                else:
                    raise ValueError, "repeated_type must is varint, bit32 or bit64."
                for i in xrang(0, n):
                    #func 会直接set_value, 不协调
                    func(reader, self._field.repeated_type)
                return
            else:
                v = reader.read_ld_raw()
        else:
            v = reader.read_ld_raw()
        self.set_value(v)

    def read_from_string(self, raw):
        reader = MemReader(raw)
        while reader.is_eof() == False:
            tag, mainType = reader.read_tag_and_type()
            if mainType not in main_type_set:
                raise ValueError, "raw may be not a protobuf's raw"
            node = self.search_sub_node(tag)
            if node == None:
                node = self.create_sub_node(tag)
                node.set_field_main_type(mainType)
            if node._field.mainType == VARINT:
                node.read_varint(reader, node._field.subType)
            elif node._field.mainType == BIT64:
                node.read_bit64(reader, node._field.subType)
            elif node._field.mainType == LENGTH_DELIMI:
                node.read_ld(reader, node._field.subType)
            elif node._field.mainType == BIT32:
                node.read_bit32(reader, node._field.subType)
            else:
                raise ValueError, "main type is UNKNOW!"





