"""
Dump backup copies of SQL tables used by these programs.

$Id: sql-dumper.py 3973 2011-09-07 01:53:12Z sra $

Copyright (C) 2009--2010  Internet Systems Consortium ("ISC")

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

import subprocess, rpki.config

cfg = rpki.config.parser(None, "yamltest", allow_missing = True)

for name in ("rpkid", "irdbd", "pubd"):

  username = cfg.get("%s_sql_username" % name, name[:4])
  password = cfg.get("%s_sql_password" % name, "fnord")

  cmd = ["mysqldump", "-u", username, "-p" + password, "--databases"]
  cmd.extend("%s%d" % (name[:4], i) for i in xrange(12))
  subprocess.check_call(cmd, stdout = open("backup.%s.sql" % name, "w"))
