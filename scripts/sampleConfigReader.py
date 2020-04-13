#!/usr/bin/env python

import os
from utils import configReader

configMap = configReader.readConfig("/home/hhuebler/data/2i/git/cvtPmiDta/scripts/whitelist.config")

print str(configMap)
