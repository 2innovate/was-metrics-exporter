# req'd for Python 2.1, default later on
from __future__ import nested_scopes
from types import DictType, ListType, IntType
import sys
import os
import logger as l
import time

# emulate Boolean
(False, True) = (0, 1)

TAG_NAMES = ["cell", "node", "server", "j2eetype", "module", 
             "label5", "label6", "label7", "label8", "label9", "label10", "label11", "label12", "label13", "label14", "label15"]

STAT_SHORT_NAMES = {
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
    new = STAT_SHORT_NAMES.get(statName)
    if new:
        return new
    return statName


@l.logEntryExit
def getTagDataTuples(perfDataEntry):
    '''
    returns list of tag tuples.
    [ (tag1-name, tag1-value), (tag2-name, tag2-value), ... ]
    '''
    rawTagString = perfDataEntry["tags"]
    
    ### TODO: access WCV_SEPARATOR
    tagsList = rawTagString.split("|")
    if len(tagsList) > len(TAG_NAMES):
        l.fatal("you need more labels in TAG_NAMES!")
    
    rtnList = []
    for x in range(len(tagsList)):
        tagName = TAG_NAMES[x]
        tagValue = tagsList[x].replace(" ", "_")
        if(x == 4):
            tagValue = translateStatName(tagValue)
        rtnList.append((tagName, tagValue))
    l.debug("raw  tags data tuples list: '%s'", rtnList)
    return rtnList


@l.logEntryExit
def getFieldDataHelper(perfDataDict):
    '''
    Returns the string with the fields and values
    '''

    def makeTuple(perfData, name, id):
        return (name + "." + id, perfData[id])

    rtnList = []
    perfName = perfDataDict["name"].replace(" ", "_")

    if (perfDataDict["classificaton"] == "CountStatistic"):
        # rtnList.append((perfName + ".count", perfDataDict["count"]))
        rtnList.append(makeTuple(perfDataDict, perfName, "count"))

    elif (perfDataDict["classificaton"] == "AverageStatistic"):
        rtnList.append(makeTuple(perfDataDict, perfName, "count"))
        rtnList.append(makeTuple(perfDataDict, perfName, "max"))
        rtnList.append(makeTuple(perfDataDict, perfName, "min"))
        rtnList.append(makeTuple(perfDataDict, perfName, "mean"))
        rtnList.append(makeTuple(perfDataDict, perfName, "total"))
        rtnList.append(makeTuple(perfDataDict, perfName, "sumOfSquares"))

    elif (perfDataDict["classificaton"] == "TimeStatistic"):
        rtnList.append(makeTuple(perfDataDict, perfName, "min"))
        rtnList.append(makeTuple(perfDataDict, perfName, "max"))
        rtnList.append(makeTuple(perfDataDict, perfName, "totalTime"))

    elif (perfDataDict["classificaton"] == "RangeStatistic"):
        rtnList.append(makeTuple(perfDataDict, perfName, "highWaterMark"))
        rtnList.append(makeTuple(perfDataDict, perfName, "lowWaterMark"))
        rtnList.append(makeTuple(perfDataDict, perfName, "integral"))
        rtnList.append(makeTuple(perfDataDict, perfName, "mean"))
        rtnList.append(makeTuple(perfDataDict, perfName, "value"))

    elif (perfDataDict["classificaton"] == "BoundedRangeStatistic"):
        rtnList.append(makeTuple(perfDataDict, perfName, "highWaterMark"))
        rtnList.append(makeTuple(perfDataDict, perfName, "lowWaterMark"))
        rtnList.append(makeTuple(perfDataDict, perfName, "integral"))
        rtnList.append(makeTuple(perfDataDict, perfName, "lowerBound"))
        rtnList.append(makeTuple(perfDataDict, perfName, "upperBound"))
        rtnList.append(makeTuple(perfDataDict, perfName, "mean"))
        rtnList.append(makeTuple(perfDataDict, perfName, "value"))

    else:
        l.fatal("Invalid classificaton in perfDataDict found: '%s'. Exiting ..." % (
            perfDataDict["classificaton"]))

    return rtnList


@l.logEntryExit
def getFieldDataTuples(perfDataEntry):
    '''
    returns list of field tuples.
    [ (field1-name, field1-value), (field2-name, field2-value), ... ]
    '''
    statsList = []
    perfDataDictList = perfDataEntry["perfdata"]
    for stats in perfDataDictList:
        statsList.extend(getFieldDataHelper(stats))
    return statsList


#
# Here comes the specific formatting code for each output FORMAT:
#

# @l.logEntryExit
def DummyFormatter():
    def formatTimeStamp(ts):
        return "Dummy-TIME-STAMP"

    def formatTags(tagData):
        return "no tags"

    def formatFields(fieldData):
        return "no field data"

    def write(perfData, timestamp):
        return "{} {} {}".format(
            formatTimeStamp(timestamp),
            formatTags(None),
            formatFields(None))

    return write


# @l.logEntryExit
def SplunkFormatter():

    def formatTimeStamp(timeStamp):
        '''
        return a Splunk readable timestamp string
        '''
        return time.strftime("%Y-%m-%d %H:%M:%S", timeStamp)

    def formatTags(perfData):
        '''
        returns a "key1=value1 key2=value2" string
        '''
        tagList = ["%s=%s" % (k, v) for (k, v) in getTagDataTuples(perfData)]
        return " ".join(tagList)

    def formatFields(perfData):
        x = getFieldDataTuples(perfData)
        fieldList = ["%s=%s" % (k, v) for (k, v) in x]
        return " ".join(fieldList)
        # return "count=42 weight=101"

    def write(perfData, timestamp):
        data = perfData
        return "{} {} {}".format(
            formatTimeStamp(timestamp),
            formatTags(perfData),
            formatFields(perfData))

    return write
