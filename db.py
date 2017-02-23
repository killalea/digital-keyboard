import atexit
import sqlite3

get_all_mappings_query = '''
SELECT * FROM mappings
'''

get_all_mapping_names_query = '''
SELECT DISTINCT mname FROM mappings
'''

get_mapping_from_name_query = '''
SELECT key, note FROM mappings
WHERE mname = "{0}"
'''

insert_mapping_query = '''
INSERT INTO mappings VALUES(?, ?, ?)
'''


class db(object):
	def __init__(self):
		super(db, self).__init__()

		self.conn = sqlite3.connect('digital-keyboard.db')
		atexit.register(self.close_connection)
		self.c = self.conn.cursor()

	def close_connection(self):
		self.conn.close()
		print "db connection closed"

	def get_all_mappings(self):
		self.c.execute(get_all_mappings_query)
		return self.c.fetchall()

	def get_all_mapping_names(self):
		self.c.execute(get_all_mapping_names_query)
		return self.c.fetchall()

	def get_mapping_from_name(self):
		self.c.execute(get_mapping_from_name_query)
		return self.c.fetchall()

	def insert_mapping_query(self, mapping, num_notes):
		self.c.executemany(insert_mapping_query, mapping)
		self.conn.commit()

