import syslog

console_echo = False

def Init(name, echo=False):
    global console_echo
    console_echo = echo
    syslog.openlog(name)

def Debug(msg):
    syslog.syslog(syslog.LOG_DEBUG, msg)
    if console_echo: print 'debug: %s' % (msg)

def Info(msg):
    syslog.syslog(syslog.LOG_INFO, msg)
    if console_echo: print 'info: %s' % (msg)

def Error(msg):
    syslog.syslog(syslog.LOG_ERR, msg)
    if console_echo: print 'error: %s' % (msg)
