import pb_node
import db
db.load_dbfile("msg.db", "enums.db")
msg = db.create_message()
root = pb_node.PBNode(msg)
s = "\x0a\x1e\x09\x01\x00\x00\x00\x00\x00\x00\x00\x12\x03\x31\x32\x33\x18\x01\x18\x02\x31\xfe\xff\xff\xff\xff\xff\xff\xff\x80\x10\x08"
root.read_from_string(s)
db.save_dbfile("msgs.db","enums.db")
