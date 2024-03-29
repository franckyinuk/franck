# Protocol implementation for handling gsocmentors.com transactions
# Author: Noah Fontes nfontes AT cynigram DOT com
# License: MIT
 
def sqlite2cookie(filename):
    from cStringIO import StringIO
    from pysqlite2 import dbapi2 as sqlite

    con = sqlite.connect(filename)

    cur = con.cursor()
    cur.execute("select host, path, isSecure, expiry, name, value from moz_cookies")

    ftstr = ["FALSE","TRUE"]

    s = StringIO()
    s.write("""\
# Netscape HTTP Cookie File
# http://www.netscape.com/newsref/std/cookie_spec.html
# This is a generated file!  Do not edit.
""")
    for item in cur.fetchall():
        s.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
            item[0], ftstr[item[0].startswith('.')], item[1],
            ftstr[item[2]], item[3], item[4], item[5]))
 
    s.seek(0)
 
    cookie_jar = cookielib.MozillaCookieJar()
    cookie_jar._really_load(s, '', True, True)
    return cookie_jar

if __name__ == "__main__":
    # symbols are avaialbe at http://www.moneyextra.com/stocks/ftse350
    sqlite2cookie()

