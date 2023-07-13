import time

def get_plural(number, unit, unit_plural = None):
    if number == 1:
        return unit
    else:
        if not unit_plural:
            unit_plural = unit + "s"
        return unit_plural
        

def humanize_time(seconds):
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    string = []
    if hours:
        string.append("%d %s" %(hours, get_plural(hours, "hour")))
    if minutes:
        string.append("%d %s" %(minutes, get_plural(minutes, "minute")))
    if seconds:
        string.append("%.1f %s" %(seconds, get_plural(seconds, "second")))
        
    return ' '.join(string)

def send_email(text, to_addrs, fromSiemens = False):
    import smtplib

    from_addr = "cambsac@yahoo.co.uk"
    if (fromSiemens):
        from_addr = "someoned@siemens.com"


    subject = "Title to set"
    text = "\n".join(text)
    text = text.replace("\n", "<br \>\n")
    html = "<html>\n<head>\n<title>%s</title></head>\n<body>\n<p>%s</p>\n</body>\n</html>" % (subject, text)
    print(html)
    message = createhtmlmail(html, text, from_addr, ",".join(to_addrs), subject)
    
    server = None
    if (not fromSiemens):
        smtp = "smtp.mail.yahoo.co.uk:587"
        login = "cambsac"
        password = "B5ac240"
        server = smtplib.SMTP(smtp)
        server.starttls()
        server.login(login , password )
    else:
        smtp = "slsmtp.ugs.com"
        server = smtplib.SMTP(smtp)
    server.sendmail(from_addr, to_addrs, message)
    server.quit()
    print("message sent")
  

def send_email2(subject, textList, to_addrs, fromSiemens = False, sender = ""):
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    # me == my email address
    # you == recipient's email address
    me = "someone@siemens.com"
    if sender != "":
        me = sender
    you = to_addrs
    
    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = me
    msg['To'] = ", ".join(you)

    # Create the body of the message (a plain-text and an HTML version).
    text = "\n".join(textList)
    text = text.replace("\n", "<br \>\n")
    html = """\
    <html>
      <head></head>
      <body>
        <p>%s</p>
      </body>
    </html>
    """ % (text)

    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(part1)
    msg.attach(part2)

    # Send the message via local SMTP server.
    server = None
    if (not fromSiemens):
        smtp = "smtp.mail.yahoo.co.uk:587"
        login = "cambsac"
        password = "B5ac240"
        server = smtplib.SMTP(smtp)
        server.starttls()
        server.login(login , password )
    else:
        smtp = "slsmtp.ugs.com"
        server = smtplib.SMTP(smtp)
    
    # sendmail function takes 3 arguments: sender's address, recipient's address
    # and message to send - here it is sent as one string.
    server.sendmail(me, you, msg.as_string())
    server.quit()

def createhtmlmail (html, text, fromaddr , toaddrs, subject):
    """Create a mime-message that will render HTML in popular
    MUAs, text in better ones"""
    import mimetools
    import cStringIO
    import MimeWriter

    out = cStringIO.StringIO() # output buffer for our message
    htmlin = cStringIO.StringIO(html)
    txtin = cStringIO.StringIO(text)

    writer = MimeWriter.MimeWriter(out)
    #
    # set up some basic headers... we put subject here
    # because smtplib.sendmail expects it to be in the
    # message body
    #
    writer.addheader("From", fromaddr)
    writer.addheader("To", toaddrs)
    writer.addheader("Subject", subject)
    writer.addheader("MIME-Version", "1.0")
    #
    # start the multipart section of the message
    # multipart/alternative seems to work better
    # on some MUAs than multipart/mixed
    #
    writer.startmultipartbody("alternative")
    writer.flushheaders()
    #
    # the plain text section
    #
    subpart = writer.nextpart()

    subpart.addheader("Content-Transfer-Encoding", "quoted-printable")
    pout = subpart.startbody("text/plain", [("charset", 'us-ascii')])
    mimetools.encode(txtin, pout, 'quoted-printable')
    txtin.close()
    #
    # start the html subpart of the message
    #
    subpart = writer.nextpart()
    subpart.addheader("Content-Transfer-Encoding", "quoted-printable")
    #
    # returns us a file-ish object we can write to
    #
    pout = subpart.startbody("text/html", [("charset", 'us-ascii')])
    mimetools.encode(htmlin, pout, 'quoted-printable')
    htmlin.close()
    #
    # Now that we're done, close our writer and
    # return the message body
    #
    writer.lastpart()
    msg = out.getvalue()
    out.close()
    #print msg
    return msg

    
class Timer(object):
    def __init__(self, verbose=False):
        self.verbose = verbose

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.end = time.time()
        self.secs = self.end - self.start
        self.msecs = self.secs * 1000  # millisecs
        if self.verbose:
            print('elapsed time: %f ms' % self.msecs)
            
class Logger(object):
    def __init__(self, log_file_name, lock):
        self.log_file_name = log_file_name
        self.lock = lock
        self.quiet_mode = False
        
    def make_error_block(self, error):
        text = "\n" + ('!'*80) + "\n"
        text += error + "\n"
        text += ('!'*80) + "\n\n"
        return text

    def my_print(self, text):
        if type(text) == type([]):
            text = '\n'.join(text)
        print(text)

    # us stands for unsafe
    def us_print_to_screen(self, text):
        if not self.quiet_mode:
            self.my_print(text)
        
    def us_print_info(self, text):
        if not self.quiet_mode:
            self.my_print(text)
        self.us_write_to_log(text)

    def us_print_error(self, error):
        text = self.make_error_block(error)
        self.my_print(text)
        self.us_write_to_log(text)

    def us_write_to_log(self, text):
        time_string = time.strftime("%Y/%m/%d") + "-" + time.strftime("%H:%M:%S") + ": "
        if type(text) == type([]):
            text = [time_string + line for line in text]
            text = '\n'.join(text)
        else:
            text = time_string + text
        file = open(self.log_file_name, "a")
        file.write(text + "\n")
        file.close()

    def print_to_screen(self, text):
        with self.lock:
            if not self.quiet_mode:
                self.my_print(text)
        
    def print_info(self, text):
        with self.lock:
            if not self.quiet_mode:
                self.my_print(text)
            self.us_write_to_log(text) #calling the unsafe version because we have already acquired the lock

    def print_error(self, error):
        text = self.make_error_block(error)
        self.print_info(text)

    def write_to_log(self, text):
        with self.lock:
            time_string = time.strftime("%Y/%m/%d") + "-" + time.strftime("%H:%M:%S") + ": "
            if type(text) == type([]):
                text = [time_string + line for line in text]
                text = '\n'.join(text)
            else:
                text = time_string + text
            file = open(self.log_file_name, "a")
            file.write(text + "\n")
            file.close()

