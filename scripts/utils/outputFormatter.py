# req'd for Python 2.1, default later on
from __future__ import nested_scopes
from types import DictType, ListType, IntType
import sys
import os
import re
import logger as l

# emulate Boolean
(False, True) = (0, 1)

TAG_NAMES = ["cell", "node", "server", "j2eetype", "module", 
             "label", "label", "label", "label", "label"]

STAT_NAMES = {
    "ARD requests": "ard",
    "client": "client",
    "DCS Statistics": "dcs",
    "Durable Subscriptions": "dsubs",
    "Garbage Collection": "gc",
    "HAManager": "ham",
    "Interceptors": "interceptors",
    "JCA Connection Pools": "jca",
    "JVM Runtime": "jvm",
    "MessageStoreStats": "msgstore",
    "Monitor": "mon",
    "Object": "obj",
    "Object Pool": "objp",
    "ORB": "orb",
    "Queues": "queues",
    "Schedulers": "schedulers",
    "server": "server",
    "Servlet Session Manager": "session",
    "SipContainerModule": "sip",
    "StatGroup": "statgroup",
    "System Data": "system",
    "Thread": "thread",
    "Thread_Pool": "threadpool",
    "Thread Pools": "threadpools",
    "Topicspaces": "topic",
    "Transaction Manager": "txm",
    "Web Applications": "apps",
    "Web services": "ws",
    "Web services Gateway": "wsg",
    "xdProcessModule": "xd",
}


def translateStatName(statName):
    new = STAT_NAMES.get(statName)
    if new:
        return new
    return statName

@l.logEntryExit
def getTagData(perfData):
    '''
    returns list of tag tuples.
    [ (tag1-name, tag1-value), (tag2-name, tag2-value), ... ]
    '''
    rawTagString = perfData["tags"]

    rtnList = []
    tagsList = rawTagString.split("|")

    for x in range(len(tagsList)):
        tagName = TAG_NAMES[x]
        tagValue = tagsList[x].replace(" ", "_")
        if(x == 4):
            tagValue = translateStatName(tagValue)

        tpl = (tagName, tagValue)
        rtnList.append(tpl)
    l.debug("raw  tags data tuples list: '%s'", rtnList)
    return rtnList


#
# Here comes the specific formatting code for each output FORMAT:
#

# @l.logEntryExit
def DummyFormatter():

    def formatTags(tagData):
        return "no tags"

    def formatFields(fieldData):
        return "no field data"

    def write(perfData):
        return "formatted by DummyFormatter: (perfData len={}) {} {}".format(
            str(len(perfData)),
            formatTags(None),
            formatFields(None))

    return write


# @l.logEntryExit
def SplunkFormatter():

    def formatTags(perfData):
        '''
        returns a "key1=value1 key2=value2" string
        '''
        tagList = ["%s=%s" % (k, v) for (k, v) in getTagData(perfData)]
        return " ".join(tagList)

    def formatFields(perfData):
        return "count=42 weight=101"

    def write(perfData):
        data = perfData
        return "formatted by SplunkFormatter: {} {}".format(
            formatTags(perfData),
            formatFields(perfData))

    return write
