import sqlite3

create_table_mappings = '''
CREATE TABLE mappings (
  mname VARCHAR(255) NOT NULL,
  key INTEGER NOT NULL,
  note INTEGER NOT NULL
)
'''

# TODO: split this table up in traditional relational style
# create_table_mappings = '''
# CREATE TABLE mappings (
#   mname VARCHAR(255) PRIMARY KEY,
#   key INTEGER NOT NULL
# )
# '''

# create_table_note_mappings = '''
# CREATE TABLE note_mappings (
#   mname VARCHAR(255),
#   note INTEGER NOT NULL,
#   FOREIGN KEY (mname) REFERENCES mappings(mname)
# )
# '''

class Mapping(object):
  conn = sqlite3.connect('mappings.db')
  c = conn.cursor()
  c.execute(create_table_mappings)
  conn.close()
