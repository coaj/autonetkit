"""
(Re)Initialize SQL tables used by these programs.

$Id: sql-cleaner.py 4415 2012-04-15 04:42:40Z sra $

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

import rpki.config, rpki.sql_schemas
from rpki.mysql_import import MySQLdb

cfg = rpki.config.parser(None, "yamltest", allow_missing = True)

for name in ("rpkid", "irdbd", "pubd"):

  username = cfg.get("%s_sql_username" % name, name[:4])
  password = cfg.get("%s_sql_password" % name, "fnord")
  
  schema = []
  for line in getattr(rpki.sql_schemas, name, "").splitlines():
    schema.extend(line.partition("--")[0].split())
  schema = " ".join(schema).strip(";").split(";")
  schema = [statement.strip() for statement in schema if statement and "DROP TABLE" not in statement]

  for i in xrange(12):

    database = "%s%d" % (name[:4], i)

    db = MySQLdb.connect(user = username, db = database, passwd = password)
    cur = db.cursor()

    cur.execute("SHOW TABLES")
    tables = [r[0] for r in cur.fetchall()]

    cur.execute("SET foreign_key_checks = 0")
    for table in tables:
      cur.execute("DROP TABLE %s" % table)
    cur.execute("SET foreign_key_checks = 1")  

    for statement in schema:
      cur.execute(statement)

    cur.close()
    db.close()
