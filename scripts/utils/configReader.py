"""
Package WasconfigReader
"""

import ConfigParser
import os
import re
import glob
import logger as l
# emulate Boolean
(False, True) = (0, 1)

# Read these *.config files
CONFIG_FILES_REQUIRED_WHITELIST = 'whitelist.config'
# discover enumeration on first level: eg "DATASOURCE3"
wh_re_enumeration = re.compile('^[A-z]+(\d+)\.', re.IGNORECASE)

ConfigReader_DEBUG = True


@l.logEntryExit
def readConfig(configFile):
    """
    reads the entire config and loads it into a dictionary, which is returned
    """
    if not os.path.isfile(configFile):
        l.error("configFile '%s' is not readable!", configFile)
        raise Exception
    config = {}
    config['WHITELIST'] = readWhiteListConfig(configFile)
    return config


@l.logEntryExit
def readWhiteListConfig(configFile):
    """
    read the admin-auth.config file
    """
    sectionData = readPropertiesFile(configFile)
    return sectionData


@l.logEntryExit
def configReaderOptionSort(string):
    """
    sorting function helper to be used by sorted()
    will _nummerically_ sort list of config entry strings:
    Example:    Datasource1
                Datasource2
                Datasource10
    """
    match = wh_re_enumeration.search(string)
    if (match) is None:
        return 0
    number = int(match.group(1))
    return number


@l.logEntryExit
def readPropertiesFile(fname):
    """
    Uses ConfigReader to read all sections in to a dictionary. Each sections options will
    be kept as nested dictionary under each section key.
    e.g.:
    {
        'WHITELIST': {
            '<j2eetype-1>': {
                '<value-1>',
                '<value-2>',
                :
                '<value-n>'
                }
            '<j2eetype-2>': {
                '<value-1>',
                '<value-2>',
                :
                '<value-n>'
                }
    }
    """
    l.debug("looking for file: '%s'", fname)
    if not os.path.isfile(fname):
        l.debug("file not found: '%s'", fname)
        return {}

    # discover comments per regex
    re_comment = re.compile('^\s*#', re.IGNORECASE)
    # discover enumeration on first level: eg "DATASOURCE3"
    re_enumeration = re.compile('^([A-z]+)(\d+)\.', re.IGNORECASE)

    reader = ConfigParser.ConfigParser()
    l.debug("reading file: '%s'", fname)
    reader.read(fname)
    # read all sections and items therein
    allSectionsMap = {}
    sectionNames = reader.sections()
    sectionNames.sort()
    for sectionName in sectionNames:
        if l.isDebugEnabled():
            l.logLF()
            l.debug("found section === %s === ", sectionName)
        sectionMap = {}
        allSectionsMap[sectionName.upper()] = sectionMap

        lastBlockNumber = -1
        expectedBlockNumber = 0
        configBlockNumber = 0
        # read all option lines from current section into sectionMap dictionary
        # eg: "datasource1.connectionpool.reaptime = 7"
        sectionOptions = reader.options(sectionName)
        # in Python 2.1 (WAS8.x) the option() lines of a configParser section may be unsorted!
        # but I cant use default sort, because Datasource1, datasource10 will be sorted before Datasource2
        if l.isHellLevelEnabled():
            for optionKey in sectionOptions:
                l.debug666("read original-ordered section/line: %-20s :  %s", sectionName, optionKey)

        sortedSectionOptions = sorted(sectionOptions, key=configReaderOptionSort)
        if l.isHellLevelEnabled():
            for optionKey in sortedSectionOptions:
                l.debug666("read num.sorted section/line: %s :\t%s", sectionName, optionKey)

        for optionKey in sortedSectionOptions:
            if (re_comment.search(optionKey)) is not None:
                l.debug666("skipping comment: %s", optionKey)
                continue
            optionValue = reader.get(sectionName, optionKey)

            # now fix the *1st* level of enumeration, if it is not done sequentially.
            # eg. when somebody declares 20 datasources, but deletes the 3rd.
            # This way, one does not need to re-enumerate all the
            # other datasource entries in the config file.
            match = re_enumeration.search(optionKey)
            if (match) is not None:
                configBlockNumber = int(match.group(2))
                if configBlockNumber > lastBlockNumber:
                    # new block found -> increase block counter
                    if l.isDebugEnabled():
                        l.logLF()
                        l.debug("=== read new config block # %d ===", configBlockNumber)
                    expectedBlockNumber = expectedBlockNumber + 1
                    lastBlockNumber = configBlockNumber

                l.debug2("config #:%2d   expected #:%2d", configBlockNumber, expectedBlockNumber)
                # check for non-sequential block numbering!
                if configBlockNumber != expectedBlockNumber:
                    l.debug("FIX block numbering: %d -> %d in option: '%s'",
                            configBlockNumber, expectedBlockNumber, optionKey)
                    optionKey = re_enumeration.sub(lambda m, num=expectedBlockNumber: "%s%s." % (m.group(1), num), optionKey)
                    # and store the original block number in special hash key:
                    originalNumberKey = "%s%d.%s" % (match.group(1), expectedBlockNumber, "__ORIGINAL_NUMBER")
                    sectionMap[originalNumberKey.upper()] = configBlockNumber

            l.debug("data: %s = %s", optionKey, optionValue)
            # finally, add key to sectionMap hash:
            sectionMap[optionKey.upper()] = optionValue

    return allSectionsMap
