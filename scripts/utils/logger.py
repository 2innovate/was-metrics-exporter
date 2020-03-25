# req'd for Python 2.1, default later on
from __future__ import nested_scopes
import sys
import os
import re


# Loglevel definitions
class LogLevels:
    OFF = 0
    FATAL = 1
    ERROR = 2
    WARN = 3
    INFO = 4
    VERBOSE = 5
    DEBUG = 6
    FINEST = 7
    ENTRY_EXIT = 8
    HELL = 9

    COLOR = {
        "NONE": "\033[0;0m",
        "RED": "\033[1;31m",
        "GREEN": "\033[1;32m",
        "YELLOW": "\033[1;33m",
        "BLUE": "\033[1;34m",
        "PURPLE": "\033[1;35m",
        "CYAN": "\033[0;36m",
        "WHITE": "\033[1;37m",
    }

    DESC = ['OFF    ', 'FATAL  ', 'ERROR  ', 'WARN   ', 'INFO   ', 'VERBOSE', 'DEBUG  ', 'FINEST ', 'ENTR_EX', 'HELL   ']
    SHORT_DESC = ['O', 'F', 'E', 'W', 'I', 'V', 'D', 'F', 'X', 'H']
    LCOLOR_DEF = [COLOR['NONE'], COLOR['RED'], COLOR['RED'], COLOR['YELLOW'], COLOR['WHITE'],
                  COLOR['GREEN'], COLOR['CYAN'], COLOR['CYAN'], COLOR['BLUE'], COLOR['PURPLE']]
    NO_COLOR_DEF = ["", "", "", "", "", "", "", "", "", ""]
    LCOLOR = LCOLOR_DEF


def whichOS():
    import os
    somePath = os.getcwd()
    if somePath[0] == '/':
        # linux or similar
        return "LINUX"
    else:
        return "UNKNOWN"


def enableColorOutput():
    # sadly, in WAS very old jython version (2.1 !!!)
    # there is no way to detemine if running interactively in a TTY
    # or if redirected to a file.
    # so coloured output can only enabled only when
    # env WASCONFIG_COLORS is set!

    # (vMajor, vMminor) = sys.version_info[0:2]
    # if (vMajor, vMminor) >= (2, 7):
    #     # sadly, this does not work in Jython 2.1 :-(
    #     try:
    #         x = sys.stdout.isatty()
    #         if x:
    #             # we're running in a terminal
    #             LogLevels.LCOLOR = LogLevels.LCOLOR_DEF
    #             info("enabling colored output for interactive env")
    #         else:
    #             debug2("%s: no colours, because not on a TTY!", m)
    #     except:
    #         warn("%s: TTY check failed.", m)
    #
    # elif os.environ.get("WASCONFIG_COLORS", "") != "":
    #     info("enabling colored output")
    #     LogLevels.LCOLOR = LogLevels.LCOLOR_DEF
    #
    LogLevels.LCOLOR = LogLevels.NO_COLOR_DEF
    if os.environ.get("WASCONFIG_COLOR", "") or os.environ.get("WASCONFIG_COLORS", ""):
        LogLevels.LCOLOR = LogLevels.LCOLOR_DEF
        info("enabling colour output")


def disableColorOutput():
    LogLevels.LCOLOR = LogLevels.NO_COLOR_DEF


def getLogLevelString(level):
    return LogLevels.DESC[level]


def getShortLogLevelString(level):
    return LogLevels.SHORT_DESC[level]


def getLogColor(level):
    return LogLevels.LCOLOR[level]


def getStdColor():
    # return NONE color
    return LogLevels.LCOLOR[0]


# helper function
def setLoglevel(level):
    global LOGLEVEL
    LOGLEVEL = level


def setLoglevelByName(logLevelName):
    logLevelName = logLevelName.upper().strip()
    if (logLevelName == "FATAL"):
        setLoglevel(LogLevels.FATAL)
    elif (logLevelName == "ERROR"):
        setLoglevel(LogLevels.ERROR)
    elif (logLevelName == "WARN"):
        setLoglevel(LogLevels.WARN)
    elif (logLevelName == "INFO"):
        setLoglevel(LogLevels.INFO)
    elif (logLevelName == "VERBOSE"):
        setLoglevel(LogLevels.VERBOSE)
    elif (logLevelName == "DEBUG"):
        setLoglevel(LogLevels.DEBUG)
    elif (logLevelName == "FINEST"):
        setLoglevel(LogLevels.FINEST)
    elif ((logLevelName == "ENTRY_EXIT") or (logLevelName == "ENTR_EX")):
        setLoglevel(LogLevels.ENTRY_EXIT)
    elif (logLevelName == "HELL"):
        setLoglevel(LogLevels.HELL)
    elif (logLevelName == "OFF"):
        setLoglevel(LogLevels.OFF)
    else:
        ##
        ## Invalid log level. Raise an exception
        exceptionString = ("Invalid Loglevel name '%s' set! supported Loglevels are: '%s'" % (logLevelName, str(LogLevels.DESC)))
        raise Exception, exceptionString


def printLoglevel():
    print "current loglevel: %s" % LogLevels().getLogLevelString(LOGLEVEL)


def getLoglevel():
    return LOGLEVEL


def testLogColors():
    setLoglevel(LogLevels.FINEST)
    error("logcolor test: ERROR")
    warn("logcolor test: WARN")
    info("logcolor test: INFO")
    verbose("logcolor test: VERBOSE")
    debug("logcolor test: DEBUG")
    debug2("logcolor test: FINEST")
    debugEE("logcolor test: ENTRY_EXIT")
    debug666("logcolor test: HELL")
    fatal("logcolor test: FATAL")


# main logging function
def isDebugEnabled():
    return (LogLevels.DEBUG <= LOGLEVEL)


def isDebug2Enabled():
    return (LogLevels.FINEST <= LOGLEVEL)


def isHellLevelEnabled():
    return (LogLevels.HELL <= LOGLEVEL)


def isVerboseEnabled():
    return (LogLevels.VERBOSE <= LOGLEVEL)


def printFrameInfo(frame, i=0):
    printf("\n++++++++++++++++++++++++++++++++++++++++++++++\n")
    printf("frameInfo: D=%d code     => %s", i, repr(frame.f_code))
    printf("frameInfo: D=%d filename => %s", i, repr(frame.f_code.co_filename))
    printf("frameInfo: D=%d function => %s", i, repr(frame.f_code.co_name))
    printf("frameInfo: D=%d lineno   => %s", i, frame.f_lineno)
    printf("++++++++++++++++++++++++++++++++++++++++++++++\n")


# define the length of the functionName log field
# prefixLen..CharsUpto(MaxLen)
prefixLen = 0
maxLen = 25

# use (maxLen+5) <<-- linenum is 4 digits + ':'
# should resolve to: "%-31s| %s"
outputFormatString = "%%-%ds| %%s" % (maxLen + 5)


def formatLogString(funcName, format):
    """
    prepend functionName to log message
    """
    return outputFormatString % (funcName, format)


def getLogCallerFuncName():
    """
    finds the function name and linenumber of parent function, i.e. the one
    calling our log function, and returns as string "funcName:lineNo |"
    """

    # frame.f_code.co_name usually returns funcName wrapped by quotes (')
    #  or '<module>' when executing the main module!

    def formatFuncName(f, maxLen, prefixLen):
        if f[0] == "'":  # and f[-1] == "'":
            f = f[1:-1]
        # this only required if there is no main() function:
        # if f == "<module>" or f == "?":
        #     f = "__main__"
        if len(f) > maxLen:
            # abbreviate function names like "func...Name" with len = maxLen!
            f = f[0:prefixLen] + ".." + f[-(maxLen - prefixLen - 2):]
        return f

    # real function is the one 2 stackframes up!
    frame = sys._getframe(2)
    # except for debugEE() - that one is called from the logDecorator!
    if frame.f_code.co_name == 'logDecorator':
        frame = frame.f_back
    tfuncName = formatFuncName(repr(frame.f_code.co_name), maxLen, prefixLen)
    return "%s:%-4d" % (tfuncName, frame.f_lineno)


def _log(loglevel, formatStr, *args):
    """
    internal log function doing the actual work.
    it should only be called from higher level log functions: warn(), info(), ...
    """
    if loglevel <= LOGLEVEL:
        # msg = "%s%s%s  %s" % (getLogColor(loglevel), getShortLogLevelString(loglevel), getStdColor(), formatStr)
        msg = "%s%s  %s%s" % (getLogColor(loglevel), getShortLogLevelString(loglevel), formatStr, getStdColor())
        printf(msg, *args)


# prints count number of linefeeds
def logLF(count=1):
    """ log count linefeeds
    """
    format = formatLogString(getLogCallerFuncName(), " ")
    for _ in range(1, count + 1):
        _log(LogLevels.INFO, format)


def fatal(format, *args):
    format = formatLogString(getLogCallerFuncName(), format)
    _log(LogLevels.FATAL, format, *args)
    raise Exception, "application encountered a fatal error"


def error(format, *args):
    format = formatLogString(getLogCallerFuncName(), format)
    _log(LogLevels.ERROR, format, *args)


def warn(format, *args):
    format = formatLogString(getLogCallerFuncName(), format)
    _log(LogLevels.WARN, format, *args)


def info(format, *args):
    format = formatLogString(getLogCallerFuncName(), format)
    _log(LogLevels.INFO, format, *args)


def verbose(format, *args):
    format = formatLogString(getLogCallerFuncName(), format)
    _log(LogLevels.VERBOSE, format, *args)


def debug(format, *args):
    format = formatLogString(getLogCallerFuncName(), format)
    _log(LogLevels.DEBUG, format, *args)


def debugEE(format, *args):
    # function will be called by logDecorator
    # for EACH enabled function call
    # so we need to speed things up.
    if LogLevels.ENTRY_EXIT > LOGLEVEL:
        return
    format = formatLogString(getLogCallerFuncName(), format)
    _log(LogLevels.ENTRY_EXIT, format, *args)


def debug2(format, *args):
    format = formatLogString(getLogCallerFuncName(), format)
    _log(LogLevels.FINEST, format, *args)


def debug666(format, *args):
    format = formatLogString(getLogCallerFuncName(), format)
    _log(LogLevels.HELL, format, *args)


def printf(format, *pargs, **kwargs):
    if pargs:
        print format % pargs
    elif kwargs:
        print format % kwargs
    else:
        print format


# this function DECORATOR works in Python 2.1!
# but requires "from __future__ import nested_scopes" to work
# and there are no @xxx annotation in Python 2.1, so you need to
# wrap each function the old way:
#
#  decoratorTestFunc1 = logEntryExit(decoratorTestFunc1)
#
def logEntryExit(func):
    """
    decorator function to log function entry and exit status.
    How to decorate in Python 2.1:

        def myFunction(...):
            ...

        myFunction = logEntryExit(myFunction)
    """
    # Alas, functools are not available in Python 2.1
    # @functools.wraps(func)
    def logDecorator(*args, **kwargs):
        p = p1 = p2 = ""
        if len(args):
            p1 = repr(args)[1:-1]
        if len(kwargs):
            p2 = repr(kwargs)[1:-1]
        if p1 or p2:
            p = "[params]: %s %s" % (p1, p2)
        debugEE(">>> %s >>>    %s", func.__name__, p)
        rc = func(*args, **kwargs)
        rrc = str(rc)
        if len(rrc) > 1000:
            debugEE("<<< %s <<<  [returned]:  %s ...", func.__name__, rrc[:1000])
        else:
            debugEE("<<< %s <<<  [returned]:  %s", func.__name__, rrc)
        return rc
    return logDecorator


def decoratorTestFunc1(arg1, arg2="default", arg3=None):
    info("INSIDE func1: arg1: %r" % arg1)
    info("INSIDE func1: arg2: %r" % arg2)
    info("INSIDE func1: arg3: %r" % arg3)
    return "%s %s %s" % (repr(arg1), repr(arg2), repr(arg3))


decoratorTestFunc1 = logEntryExit(decoratorTestFunc1)


def decoratorTestFunc2():
    info("INSIDE func2: no args")
    return "TESTFUNCTION2 says 'Hello'!"


decoratorTestFunc2 = logEntryExit(decoratorTestFunc2)


def decoratorTestFunc3(hello, name=2, foo="bar"):
    info("INSIDE func3: args: %s %s! I say '%s'", hello, name, foo)


decoratorTestFunc3 = logEntryExit(decoratorTestFunc3)


# do a simple unit test of logDecorator functionality
def runDecoratorTest():
    setLoglevel(LogLevels.ENTRY_EXIT)
    # args + default args
    result = decoratorTestFunc1("Kevin!")
    info("decoratorTestFunc1() result : %s", result)

    # all args specified
    result = decoratorTestFunc1("Kevin", "Stuart", "love Grue")
    info("decoratorTestFunc1() result : %s", result)

    # no args
    result = decoratorTestFunc2()
    info("decoratorTestFunc2() result : %s", result)

    # args + kwargs, but no return value
    result = decoratorTestFunc3("Hey", name="You", foo="baz")
    info("decoratorTestFunc3 result : %s", result)
    fatal("End of Decorator Testing.")


# default loglevel
LOGLEVEL = LogLevels.VERBOSE
enableColorOutput()
