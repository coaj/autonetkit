"""
Automated setup of all the pesky SQL stuff we need.  Prompts for MySQL
root password, pulls other information from rpki.conf.

$Id: rpki-sql-setup.py 4435 2012-04-18 18:17:54Z sra $

Copyright (C) 2009--2011  Internet Systems Consortium ("ISC")

Permission to use, copy, modify, and distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND ISC DISCLAIMS ALL WARRANTIES WITH
REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
AND FITNESS.  IN NO EVENT SHALL ISC BE LIABLE FOR ANY SPECIAL, DIRECT,
INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE
OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
PERFORMANCE OF THIS SOFTWARE.
"""

import os, getopt, sys, rpki.config, getpass, warnings

import rpki.sql_schemas

from rpki.mysql_import import MySQLdb

def read_schema(name):
  """
  Convert an SQL file into a list of SQL statements.
  """
  lines = []
  for line in getattr(rpki.sql_schemas, name, "").splitlines():
    line = " ".join(line.split())
    if line and not line.startswith("--"):
      lines.append(line)

  return [statement.strip() for statement in " ".join(lines).rstrip(";").split(";") if statement.strip()]

def sql_setup(name):
  """
  Create a new SQL database and construct all its tables.
  """
  database = cfg.get("sql-database", section = name)
  username = cfg.get("sql-username", section = name)
  password = cfg.get("sql-password", section = name)
  schema = read_schema(name)

  print "Creating database", database
  cur = rootdb.cursor()
  try:
    cur.execute("DROP DATABASE IF EXISTS %s" %  database)
  except Exception:
    pass
  cur.execute("CREATE DATABASE %s" % database)
  cur.execute("GRANT ALL ON %s.* TO %s@localhost IDENTIFIED BY %%s" % (database, username), (password,))
  rootdb.commit()

  db = MySQLdb.connect(db = database, user = username, passwd = password)
  cur = db.cursor()
  for statement in schema:
    if statement.upper().startswith("DROP TABLE"):
      continue
    if verbose:
      print "+", statement
    cur.execute(statement)
  db.commit()
  db.close()

cfg_file = None

verbose = False

opts, argv = getopt.getopt(sys.argv[1:], "c:hv?", ["config=", "help", "verbose"])
for o, a in opts:
  if o in ("-h", "--help", "-?"):
    print __doc__
    sys.exit(0)
  if o in ("-v", "--verbose"):
    verbose = True
  if o in ("-c", "--config"):
    cfg_file = a

cfg = rpki.config.parser(cfg_file, "myrpki")

rootdb = MySQLdb.connect(db = "mysql", user = "root", passwd = getpass.getpass("Please enter your MySQL root password: "))

if cfg.getboolean("start_irdbd", False):
  sql_setup("irdbd")

if cfg.getboolean("start_rpkid", False):
  sql_setup("rpkid")

if cfg.getboolean("start_pubd",  False):
  sql_setup("pubd")

rootdb.close()
