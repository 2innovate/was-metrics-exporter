# req'd for Python 2.1, default later on
from __future__ import nested_scopes
from types import DictType, ListType, IntType
import sys
import os
import re
import logger as l

# emulate Boolean
(False, True) = (0, 1)


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

    def formatTags(tagData):
        return "some tags for Splunk"

    def formatFields(fieldData):
        return "count=42 weight=101"

    def write(perfData):
        return "formatted by SplunkFormatter: (perfData len={}) {} {}".format(
            str(len(perfData)),
            formatTags(None),
            formatFields(None))

    return write
