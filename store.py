#!/usr/bin/env python
# -*- coding: utf-8 -*-

## Create a db and store populates with CSVs##

from sqlite3 import dbapi2 as sq3
import os
import pandas as pd

ourschema = '''
DROP TABLE IF EXISTS 'nodes';
DROP TABLE IF EXISTS 'nodes_tags';
DROP TABLE IF EXISTS 'ways';
DROP TABLE IF EXISTS 'ways_tags';
DROP TABLE IF EXISTS 'ways_nodes';
CREATE TABLE nodes (
    id INTEGER PRIMARY KEY NOT NULL,
    lat REAL,
    lon REAL,
    user TEXT,
    uid INTEGER,
    version INTEGER,
    changeset INTEGER,
    timestamp TEXT
);

CREATE TABLE nodes_tags (
    id INTEGER,
    key TEXT,
    value TEXT,
    type TEXT,
    FOREIGN KEY (id) REFERENCES nodes(id)
);

CREATE TABLE ways (
    id INTEGER PRIMARY KEY NOT NULL,
    user TEXT,
    uid INTEGER,
    version TEXT,
    changeset INTEGER,
    timestamp TEXT
);

CREATE TABLE ways_tags (
    id INTEGER NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    type TEXT,
    FOREIGN KEY (id) REFERENCES ways(id)
);

CREATE TABLE ways_nodes (
    id INTEGER NOT NULL,
    node_id INTEGER NOT NULL,
    position INTEGER NOT NULL,
    FOREIGN KEY (id) REFERENCES ways(id),
    FOREIGN KEY (node_id) REFERENCES nodes(id)
);'''

PATHSTART="."
dbfile = "warsaw_poland.db"
def get_db(dbfile):
	'''create the db'''
	sqlite_db = sq3.connect(os.path.join(PATHSTART, dbfile))
	return sqlite_db

def init_db(dbfile, schema):
    """Creates the database tables."""
    db = get_db(dbfile)
    db.cursor().executescript(schema)
    db.commit()
    return db

#Initiate the Database 
db=init_db(dbfile, ourschema)
print('Initiated {}'.format(dbfile))

#Read the CSV's and populate with Pandas(if_exist=replace instead of =append solved the IS NULL error)
for f in os.listdir('./CSV_Files/'):
    df=pd.read_csv("./CSV_Files/{}".format(f), sep=',', encoding='utf-8')
    
    df.to_sql(f[14:-4], db, if_exists="replace", index=False, schema=ourschema)
    print ('{} populated with {} succesfully!'.format(dbfile,f))