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

COUNTSTATISTIC_VALUES = ["count"]
AVERAGESTATISTIC_VALUES = ["count", "max", "min", "mean", "total", "sumOfSquares"]
TIMESTATISTIC_VALUES = ["min", "max", "totalTime"]
RANGESTATISTIC_VALUES = ["highWaterMark", "lowWaterMark", "integral", "mean", "value"]
BOUNDEDRANGESTATISTIC_VALUES = ["highWaterMark", "lowWaterMark", "integral", "lowerBound", "upperBound", "mean", "value"]

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
def getJ2eeType(whitelistDict, tags, toUpper = False):
    '''
    Returns the j2eetype of the tags string
    '''

    whitelistKeys = whitelistDict.keys()
    l.debug("whitelist keys are: '%s'" % (str(whitelistKeys)))
    tagsList = tags.split(NODE_SEPARATOR)
    for tag in tagsList:
        l.debug("Checking if tag '%s' is in whitelistKeys" % (tag))
        if (tag.upper() in whitelistKeys):
            if (toUpper == True):
                return tag.upper()
            else:
                return tag
    ##
    ## None of the tags is in the whitelist dictionary
    return None


@l.logEntryExit
def whitelistEntryForJ2eeType(perfDataEntry, whitelistDict = None):
    '''
    Returns an empty {} if there is no whitelist i.e. all data is to be returned.
    Returns None if the perfDataEntry is to be ignored
    Returns the whitelist dictionary of the white listed j2eetype
    '''

    if (whitelistDict):
        whitelistKeys = whitelistDict.keys()
        l.debug("whitelist keys are: '%s'" % (str(whitelistKeys)))
        tagsList = perfDataEntry["tags"].split(NODE_SEPARATOR)
        for tag in tagsList:
            l.debug("Checking if tag '%s' is in whitelistKeys" % (tag))
            if (tag.upper() in whitelistKeys):
                return whitelistDict[tag.upper()]
        ##
        ## None of the tags is in the whitelist dictionary
        return None
    else:
        ##
        ## No whitelist everything is added to the output
        l.debug ("No whitelist provided! Returning {}!")
        return {}


@l.logEntryExit
def whitelistedJ2eeType(perfDataEntry, whitelistDict = None):
    '''
    Returns True if the J2eeType of the tags is whiteListed; False otherwise
    '''
    if (whitelistEntryForJ2eeType(perfDataEntry, whitelistDict) is not None):
        return True
    else:
        return False


@l.logEntryExit
def getTagDataTuples(perfDataEntry):
    '''
    returns list of tag tuples.
    [ (tag1-name, tag1-value), (tag2-name, tag2-value), ... ]
    '''
    rawTagString = perfDataEntry["tags"]

    tagsList = rawTagString.split(NODE_SEPARATOR)
    if len(tagsList) > len(TAG_NAMES):
        l.fatal("you need more labels in TAG_NAMES!")

    rtnList = []
    for x in range(len(tagsList)):
        tagName = TAG_NAMES[x]
        tagValue = tagsList[x].replace(" ", "_")
        if(x == 3):
            tagValue = translateStatName(tagValue)
        rtnList.append((tagName, tagValue))
    l.debug("raw  tags data tuples list: '%s'", rtnList)
    return rtnList


@l.logEntryExit
def isWhitelisted(j2eeType, perfName, perfValueName, whitelistDict=None):
    '''
    Checks of the perfName.perfValueName is supported as per the whitelist dictionarey.
    Returns True if the column should be added to the output strean. False otherwise
    '''
    ##
    ## convert all to upper case
    j2eeType = j2eeType.upper()
    perfName = perfName.upper()
    perfValueName = perfValueName.upper()
    l.debug("isWhitelisted: j2eeType: '%s', perfName: '%s', perfValueName: '%s', whitelistDict: '%s'" %
        (j2eeType, perfName, perfValueName, str(whitelistDict)))
    ##
    ## whiltelistDict is None or {}
    if (not whitelistDict):
        l.debug("whitelistDict is None or empty --> returning True")
        return True
    else:
        l.debug("whitelistDict is NOT None or empty")
        ##
        ## if the j2eeType is missing in the whitelistDict this type should be omitted
        j2eeTypeDict = whitelistDict.get(j2eeType)
        l.debug("Whitelist for j2eeType: '%s' is: '%s'" % (j2eeType, str(j2eeTypeDict)))
        if (j2eeTypeDict == None):
            return False
        else:
            ##
            ## If there are no specific values for the j2eeType we include all values
            if (len(j2eeTypeDict.keys()) == 0):
                l.debug("Retruning True as len(j2eeTypeDict.keys() = 0")
                return True
            else:
                ##
                ## If the specific counter is missing or not 'true' wen omit the value
                j2eeTypeDictKey = "%s.%s" % (perfName, perfValueName)
                if ((j2eeTypeDict.get(j2eeTypeDictKey) == None) or (j2eeTypeDict.get(j2eeTypeDictKey).upper() != "TRUE")):
                    l.debug("Returning False as j2eeTypeDict.get(%s) is: '%s'" % (j2eeTypeDictKey, j2eeTypeDict.get(j2eeTypeDictKey)))
                    return False
                else:
                    l.debug("Returning True as j2eeTypeDict.get(%s) is: '%s'" % (j2eeTypeDictKey, j2eeTypeDict.get(j2eeTypeDictKey)))
                    return True


@l.logEntryExit
def getFieldDataHelper(perfDataDict, perfJ2eeType, whitelistDict = None):
    '''
    Returns the string with the fields and values
    '''

    def makeTuple(perfData, name, id):
        return (name + "." + id, perfData[id])

    rtnList = []
    perfName = perfDataDict["name"].replace(" ", "_")

    if (perfDataDict["classificaton"] == "CountStatistic"):
        for value in COUNTSTATISTIC_VALUES:
            if (isWhitelisted(perfJ2eeType, perfDataDict["name"], value, whitelistDict) == True):
                # rtnList.append((perfName + ".count", perfDataDict["count"]))
                rtnList.append(makeTuple(perfDataDict, perfName, value))

    elif (perfDataDict["classificaton"] == "AverageStatistic"):
        for value in AVERAGESTATISTIC_VALUES:
            if (isWhitelisted(perfJ2eeType, perfDataDict["name"], value, whitelistDict) == True):
                rtnList.append(makeTuple(perfDataDict, perfName, value))
    elif (perfDataDict["classificaton"] == "TimeStatistic"):
        for value in TIMESTATISTIC_VALUES:
            if (isWhitelisted(perfJ2eeType, perfDataDict["name"], value, whitelistDict) == True):
                rtnList.append(makeTuple(perfDataDict, perfName, value))

    elif (perfDataDict["classificaton"] == "RangeStatistic"):
        for value in RANGESTATISTIC_VALUES:
            if (isWhitelisted(perfJ2eeType, perfDataDict["name"], value, whitelistDict) == True):
                rtnList.append(makeTuple(perfDataDict, perfName, value))

    elif (perfDataDict["classificaton"] == "BoundedRangeStatistic"):
        for value in BOUNDEDRANGESTATISTIC_VALUES:
            if (isWhitelisted(perfJ2eeType, perfDataDict["name"], value, whitelistDict) == True):
                rtnList.append(makeTuple(perfDataDict, perfName, value))

    else:
        l.fatal("Invalid classificaton in perfDataDict found: '%s'. Exiting ..." % (
            perfDataDict["classificaton"]))
        raise Exception

    return rtnList


@l.logEntryExit
def getFieldDataTuples(perfDataEntry, whitelistDict = None):
    '''
    returns list of field tuples.
    [ (field1-name, field1-value), (field2-name, field2-value), ... ]
    '''
    statsList = []
    perfDataDictList = perfDataEntry["perfdata"]
    perfJ2eeType = getJ2eeType(whitelistDict, perfDataEntry["tags"], True)
    for stats in perfDataDictList:
        statsList.extend(getFieldDataHelper(stats, perfJ2eeType, whitelistDict))
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

    def formatFields(fieldData, whitelistDict=None):
        return "no field data"

    def write(perfDataList, timestamp, whitelistDict=None):
        '''
        main formatter function: returns a string of formatted entries
        '''
        entries = []
        for perfEntry in perfDataList:
            if (whitelistedJ2eeType(perfEntry, whitelistDict) == True):
                l.debug("Writing output record as j2eeType is whitelisted")
                formattedEntry = "{} {} {}".format(
                    formatTimeStamp(timestamp),
                    formatTags(None),
                    formatFields(None, whitelistDict)
                )
                entries.append(formattedEntry)
                l.debug(formattedEntry)
            else:
                l.debug("Output record not written as j2eeType: '%s' is not whitelisted" % (perfEntry["tags"]))
        l.verbose("Number of rows returned: %d" % (len(entries)))
        returnedObj = "\n".join(entries)
        return returnedObj

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

    def formatFields(perfData, whitelistDict=None):
        x = getFieldDataTuples(perfData, whitelistDict)
        fieldList = ["%s=%s" % (k, v) for (k, v) in x]
        return " ".join(fieldList)
        # return "count=42 weight=101"

    def write(perfDataList, timestamp, whitelistDict=None):
        '''
        main formatter function: returns a string of formatted entries
        '''
        entries = []
        for perfEntry in perfDataList:
            if (whitelistedJ2eeType(perfEntry, whitelistDict) == True):
                l.debug("Writing output record as j2eeType is whitelisted")
                formattedEntry = "{} {} {}".format(
                    formatTimeStamp(timestamp),
                    formatTags(perfEntry),
                    formatFields(perfEntry, whitelistDict)
                    )
                entries.append(formattedEntry)
                l.debug(formattedEntry)
            else:
                l.debug("Output record not written as j2eeType: '%s' is not whitelisted" % (perfEntry["tags"]))

        l.verbose("Number of rows returned: %d" % (len(entries)))
        returnedObj = "\n".join(entries)
        return returnedObj

    return write


@l.logEntryExit
def InfluxFormatter():

    @l.logEntryExit
    def getMeasurement(perfData):
        '''
        Returns the measurement name based on the tagsString
        '''
        return perfData["tags"].split(NODE_SEPARATOR)[0]


    def formatTags(perfData):
        '''
        returns a "key1=value1 key2=value2" string
        '''
        tagList = ["%s=%s" % (k, v) for (k, v) in getTagDataTuples(perfData)]
        return ",".join(tagList)


    def formatFields(perfData, whitelistDict):
        x = getFieldDataTuples(perfData, whitelistDict)
        fieldList = ["%s=%s" % (k, v) for (k, v) in x]
        return ",".join(fieldList)
        # return "count=42,weight=101"

    def write(perfDataList, timestamp, whitelistDict=None):
        '''
        main formatter function: returns a string of formatted entries
        '''
        unixTime = str(time.mktime(timestamp)).replace(".", "") + "00"
        l.debug("influxFormatter.write: timestamp:'%s' , unixTime: '%s'", str(timestamp), unixTime)

        entries = []
        for perfEntry in perfDataList:
            if (whitelistedJ2eeType(perfEntry, whitelistDict) == True):
                l.debug("Writing output record as j2eeType is whitelisted")
                formattedEntry = "{},{} {} {}".format(
                    getMeasurement(perfEntry),
                    formatTags(perfEntry),
                    formatFields(perfEntry, whitelistDict),
                    unixTime
                    )
                entries.append(formattedEntry)
                l.debug("Influx formattedEntry: '%s" % (formattedEntry))
            else:
                l.debug("Output record not written as j2eeType: '%s' is not whitelisted" % (perfEntry["tags"]))


        l.verbose("Number of rows returned: %d" % (len(entries)))
        returnedObj = "\n".join(entries)
        return returnedObj

    return write
##
## Some globals
NODE_SEPARATOR = "|"
