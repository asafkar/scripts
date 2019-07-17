#!/tools/bin/python3.6


class Spaces(object):

	def __init__(self, space_type, name, space_addr, bits, description):
		self.name = name
		self.space_type = space_type
		self.space_addr = space_addr
		self.bits = bits
		self.description = description


class Register(object):

	def __init__(self, name: object, addr: object, bits: object, RW: object) -> object:
		self.name = name
		self.addr = addr
		self.bits = bits
		self.RW = RW
		self.fields = []

	def add_fields(self, field):
		field.bits = field.bits.strip()
		if ":" not in field.bits:
			num = field.bits.strip("[]")
			field.bits = "["+num+":"+num+"]"
		self.fields.append(field)

	def sort_fields(self):
		self.fields.sort(key=lambda x: int(x.bits.strip("[]").split(":")[0]), reverse=False)

	def get_name(self):
		return self.name


class Field(object):

	def __init__(self, name, bits, reset_val, comment):
		self.name = name
		self.bits = bits
		self.reset_val = reset_val
		self.comment = comment

