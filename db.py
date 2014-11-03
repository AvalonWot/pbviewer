import database_pb2

_mem_msgs = {}
_mem_enums = {}

def get_message(msg_id):
    if msg_id not in _mem_msgs.keys():
        return None
    return _mem_msgs[msg_id][1]

def get_message_name(msg_id):
    if msg_id not in _mem_msgs.keys():
        return None
    return _mem_msgs[msg_id][0]

def get_enum(enum_id):
    if enum_id not in _mem_enums.keys():
        return None
    return _mem_enums[enum_id][1]

def get_enum_name(enum_id):
    if enum_id not in _mem_enums.keys():
        return None
    return _mem_enums[enum_id][0]

def get_message_ids():
    return _mem_msgs.keys()

def get_last_id():
    ids = _mem_msgs.keys()
    if (len(ids) == 0):
        return 0
    ids.sort()
    return ids[len(ids) - 1] + 1

def create_message(msg_id=None, name=None):
    if msg_id == None:
        msg_id = get_last_id()
    if name == None:
        name = "unkown_message_{0}".format(msg_id)
    if msg_id in _mem_msgs.keys():
        return None
    msg = database_pb2.pb_message()
    _mem_msgs[msg_id] = (name, msg)
    return msg

# def _create_pb_field(db_field):
#     mem_field = PBField()
#     mem_field.name = db_field.name
#     mem_field.tag = db_field.tag
#     mem_field.mainType = db_field.mainType
#     mem_field.subType = db_field.subType
#     mem_field.prefix = db_field.prefix
#     mem_field.message_id = None
#     if db_field.HasField('message_id'):
#         mem_field.message_id = db_field.message_id
#     mem_field.enum_id = None
#     if db_field.HasField('enum_id'):
#         mem_field.enum_id = db_field.enum_id
#     return mem_field

# def _create_pb_message(db_msg):
#     mem_msg = PBMessage()
#     for field in db_msg.fields:
#         if field.tag in mem_msg.tags:
#             raise ValueError, "db msg fields tag repeated. {0}".format(db_msg.name)
#         mem_msg.tags.append(field.tag)
#         mem_msg.fields.append(field)

def _db_msg_to_mem_msg(msgs):
    _mem_msgs.clear()
    for db_msg in msgs.entrys:
        k = db_msg.id
        kname = db_msg.name
        if k in _mem_msgs.keys():
            raise ValueError, "db msg key : ({0}, {1}) repeated.".format(k, kname)
        _mem_msgs[k] = (kname, db_msg.msg)

def _load_msg_from_file(mgs_file):
    db_msgs = database_pb2.db_messages()
    with open(mgs_file, 'rb') as f:
        data = f.read()
        db_msgs.ParseFromString(data)
    _db_msg_to_mem_msg(db_msgs)
    #todo : check the tags and fields

def _db_enum_to_mem_enum(enums):
    _mem_enums.clear()
    for db_enum in enums.entrys:
        k = db_enum.id
        kname = db_enum.name
        if k in _mem_enums.keys():
            raise ValueError, "db enum key : ({0}, {1}) repeated.".format(k, kname)
        _mem_enums[k] = (kname, db_enum.enum)

def _load_enum_from_file(enum_file):
    db_enums = database_pb2.db_enums()
    with open(enum_file, 'rb') as f:
        data = f.read()
        db_enums.ParseFromString(data)
    _db_enum_to_mem_enum(db_enums)

# @ mgs_file : msg database file name
# @ enum_file : enum database file name
def load_dbfile(mgs_file, enum_file):
    _load_enum_from_file(enum_file)
    _load_msg_from_file(mgs_file)

def _mem_msgs_to_db_msgs(db_msgs):
    for i in _mem_msgs.keys():
        entry = db_msgs.entrys.add()
        entry.id = i
        entry.name = _mem_msgs[i][0]
        entry.msg.CopyFrom(_mem_msgs[i][1])

def _save_msgs_to_file(msgs_file):
    db_msgs = database_pb2.db_messages()
    _mem_msgs_to_db_msgs(db_msgs)
    with open(msgs_file, 'wb') as f:
        data = db_msgs.SerializeToString()
        f.write(data)

def _mem_enum_to_db_enum(db_enums):
    for i in _mem_enums.keys():
        entry = db_enums.entrys.add()
        entry.id = i
        entry.name = _mem_enums[i][0]
        entry.enum.CopyFrom(_mem_enums[i][1])

def _save_enums_to_file(enums_file):
    db_enums = database_pb2.db_enums()
    _mem_enum_to_db_enum(db_enums)
    with open(enums_file, 'wb') as f:
        data = db_enums.SerializeToString()
        f.write(data)

def save_dbfile(msgs_file, enums_file):
    _save_enums_to_file(enums_file)
    _save_msgs_to_file(msgs_file)