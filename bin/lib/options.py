# req'd for Python 2.1, default later on
from __future__ import nested_scopes
from types import DictType, ListType, IntType
import sys
import os
import re
import getopt
import logger as l
import json
import urllib
import urllib2
import httplib

# emulate Boolean
(False, True) = (0, 1)


@l.logEntryExit
def printUsage(scriptName):
    '''
    print cmd usage
    '''
    usageStr = """
    Usage: {scriptName} [ --help (this information) ]

                        [ --xml |-x <perfServletXmlFile>
                        [ --url |-u <perfServletUrl>  [--seconds|-s <seconds>] [--wasUser <was_user> --wasPassword <wasPassword>] ]
                        [ --cell|-c <was_cell_name>]

                        [ --json|-j <json_outfile>]
                        [--noempty|-n]
                        [--omitSummary|-o ]

                        [--influxUrl|-i <url> --influxDb|-d <dbName>]  [-U|--targetUser <user> -P|--targetPwd <password>]

                        [ --outputFile <file-name> ]
                        [ --outputFormat  {{ "JSON" | "SPLUNK" | "DUMMY" }} ]
                        [ --replace|-r]
                        [ --outputConfig <config-file-name> ]

    whereby:
        <perfServletXmlFile>    name of the file with the WAS performance servlet output. Mutual exclusise with <perfServletXmlFile>"
        <perfServletUrl>        full URL of the performance servlet to get the data. For example:"
                                    http://<host>:<port>/wasPerfTool/servlet/perfservlet?node=<nodeName>&server=<serverName>&module=connectionPoolModule+jvmRuntimeModule"
        <seconds>               interval in seconds between fetching <perfServletUrl>"
        <json_outfile>          name of the file to which the JSON output will be written"

    optional:"
        <was_cell_name>         name of the WAS cell being used as the root of the tags. Defaults to: \"cell\""
        <--noempty|-n>          remove empty metrics. Defaults to false"
        <--replace|-r>          replace the <json_outfile> if the file exists. Defaults to false"
        <--omitSummary|-o>      omit summary measurement like for example measurement for JDBC providers"
        <--influxUrl|-i>        rest URL for InfluxDb to which data should be posted"
        <--influxDb|-d>         influxDb database to which data should be posted. You might attach a retention policy like: \n\t\t\t\t\t\t\"CREATE RETENTION POLICY TWO_WEEKS ON pmidata DURATION 2w REPLICATION 1\""
        <--targetUser|-U>       user name to authenticate on the target platform (for example influxDb)"
        <--targetPwd|-d>        password being used to authenticate on the target platform (for example influxDb)"
        <--wasUser>             user name to authenticate against WebSphere to retrieve the performance servlet data"
        <--wasPassword>         password to authenticate against WebSphere to retrieve the performance servlet data"
        <--outputFile>          output filename"
        <--outputConfig>        configuration file name to configure output columns"
    """
    print(usageStr.format(scriptName=scriptName))


SHORTOPTS = "hx:j:c:nri:d:u:os:U:P:f:O:"
LONGOPTS = ["help", "xml=", "json=", "cell=", "noempty", "replace", "influxUrl=", "influxDb=", "url=", "omitSummary", "seconds=", "targetUser=", "targetPwd=", "wasUser=", "wasPassword=", "outputFile=", "outputFormat=", "outputConfig="]


@l.logEntryExit
def getUrlSchema(perfServletUrl):
    '''
    Returns the schema of an Url
    '''
    return re.sub(r"^(.*?):.*", r"\1", perfServletUrl)


@l.logEntryExit
def getHostFromUrl(perfServletUrl):
    '''
    Returns the host of an Url
    '''
    return re.sub(r"^.*?\/\/(.*?)[:\/].*", r"\1", perfServletUrl)


@l.logEntryExit
def getPortFromUrl(perfServletUrl):
    '''
    Returns the port of an Url
    '''
    l.debug("perfServletUrl is: '%s'" % (perfServletUrl))
    port = re.sub(r"^.*?\/\/.*?\:([0-9]+)?(\/)?(.*)", r"\1", perfServletUrl)
    l.debug("port is: '%s'" % (port))
    if (port == perfServletUrl):
        return None
    else:
        return port


@l.logEntryExit
def getUriFromUrl(nexusUrl):
    '''
    Returns the URI of an Url
    '''
    uri = re.sub(r"^.*?\/\/.*?[:0-9]?\/(.*)$", r"\1", nexusUrl)
    if (uri == nexusUrl):
        return ""
    else:
        if (not uri.startswith("/")):
            uri = "/" + uri
        return uri


@l.logEntryExit
def splitHttpUrlString(urlString):
    '''
    Takes an URL String like for example http://localhost:8086 and returns a tuple of (schema, host, port)
    '''
    l.debug("Splitting URL String: '%s'" % (urlString))

    urlSchema = getUrlSchema(urlString)
    l.debug("urlSchema='%s'" % (urlSchema))
    ##
    ## Only http and https URLs are supported
    if (not urlSchema in ("http", "https")):
        l.error("The URL schema '%s' is not supported" % (urlSchema))
        raise Exception, 'Unsupported URL schema found'

    urlHost = getHostFromUrl(urlString)
    l.debug("urlHost='%s'" % (urlHost))
    urlPort = getPortFromUrl(urlString)
    l.debug("urlPort='%s'" % (urlPort))
    ##
    ## Get the port or set the defauls port if none is provided
    if not urlPort:
        if (urlSchema == HTTP_SCHEMA):
            urlPort = '80'
        elif(urlSchema == HTTPS_SCHEMA):
            urlPort = '443'
        else:
            pass
    l.debug("urlSchema: '%s'; urlHost: '%s'; urlPort: '%s'" % (urlSchema, urlHost, urlPort))

    return (urlSchema, urlHost, urlPort)


@l.logEntryExit
def parseArguments(scriptName, sysArgv):
    try:
        opts, args = getopt.getopt(sysArgv, SHORTOPTS, LONGOPTS)
        l.debug("Got the following paramters: opts:'%s'; args: '%s'" %
                (str(opts), str(args)))
    except getopt.GetoptError, err:
        printUsage(scriptName)
        l.error(">> GETOPT exception: '%s'" % (str(err)))
        sys.exit(2)
    ##
    ## Check the parameters being passed
    try:
        parmDict = getParmDict(opts, scriptName)
        checkParm(parmDict, scriptName)
    except (Exception), err:
        printUsage(scriptName)
        l.fatal("\n>> Caught exception in: " + str(err) + " by checkParm\n\n")
    ##
    ## Copy the parameter values to the variables
    return parmDictToTuple(parmDict)


@l.logEntryExit
def getParmDict(opts, scriptName):
    '''
    Returns a dictionary of the parameters. Key is the long option without '-'s and data is the value
    '''
    if (len(opts) == 0):
        printUsage(scriptName)
        sys.exit(-1)

    rtnDict = {}
    l.debug("Setting default values for optional parameters")
    rtnDict["noempty"] = False
    rtnDict["replace"] = False
    rtnDict["omitSummary"] = False
    rtnDict["cell"] = "cell"
    rtnDict["seconds"] = 0

    l.debug("Copying CLI options to parameter dictionary ...")
    for option, value in opts:
        l.debug("option: '%s'; value: '%s'" % (option, value))
        if option in ("-?", "--help"):
            rtnDict["help"] = value
        elif option in ("-x", "--xml"):
            rtnDict["xml"] = value
        elif option in ("-j", "--json"):
            rtnDict["json"] = value
        elif option in ("-c", "--cell"):
            rtnDict["cell"] = value
        elif option in ("-n", "--noempty"):
            rtnDict["noempty"] = True
        elif option in ("-r", "--replace"):
            rtnDict["replace"] = True
        elif option in ("-i", "--influxUrl"):
            rtnDict["influxUrl"] = value
        elif option in ("-d", "--influxDb"):
            rtnDict["influxDb"] = value
        elif option in ("-o", "--omitSummary"):
            rtnDict["omitSummary"] = True
        elif option in ("-u", "--url"):
            rtnDict["url"] = value
        elif option in ("-s", "--seconds"):
            rtnDict["seconds"] = int(value)
        elif option in ("-U", "--targetUser"):
            rtnDict["user"] = value
        elif option in ("-P", "--targetPwd"):
            rtnDict["password"] = value
        elif option in ("--wasUser"):
            rtnDict["wasUser"] = value
        elif option in ("--wasPassword"):
            rtnDict["wasPassword"] = value
        elif option in ("--outputFile", "-f"):
            rtnDict["outputFile"] = value
        elif option in ("--outputFormat", "-O"):
            rtnDict["outputFormat"] = value
        elif option in ("--outputConfig"):
            rtnDict["outputConfig"] = value

        else:
            l.error("Unsupported option '%s' provided. Exiting ..." % (option))
            sys.exit(1)

    return rtnDict


@l.logEntryExit
def getHttpConnection(urlSchema, urlHost, urlPort):
    '''
    returns the HTTP connection object
    '''
    l.debug("urlSchema: '%s'; urlHost: '%s'; urlPort: '%s'" % (urlSchema, urlHost, urlPort))
    if (urlSchema == HTTP_SCHEMA):
        conn = httplib.HTTPConnection(urlHost, port=urlPort, timeout=3, strict=1)
    else:
        conn = httplib.HTTPSConnection(urlHost, port=urlPort, timeout=3, strict=1)
    ##
    ## Connection successfull?
    ##
    ## Return the connection object
    return conn


@l.logEntryExit
def buildQueryString(**kwargs):
    '''
    Returns the encoded query string for the keyword list
    '''
    debugString = ""
    rtnString = ""
    rtnDict = {}
    ##
    ## Build a debug string
    for key, value in kwargs.items():
        debugString += "'%s'='%s';" % (str(key), str(value))
    l.debug("debugString: '%s'" % (debugString))
    ##
    ## Build the query String
    for key, value in kwargs.items():
        ##
        ## Only if there is a value
        if ((value != None) and (value != "")):
            rtnDict[key] = value

    l.debug("Query string unencoded: '%s'" % (str(rtnDict)))
    rtnString = urllib.urlencode(rtnDict)
    if (rtnString != ""):
        rtnString = "?" + rtnString
    l.debug("Query string encoded: '%s'" % (rtnString))
    ##
    ## Return the encoded string
    return rtnString


@l.logEntryExit
def checkParm(parmDict, scriptName):
    '''
    Checks and verifies the provided parameters
    '''
    l.debug("Start checking parameters")
    xml = jsonFile = influxUrl = influxDb = url = targetUser = targetPwd = wasUser = wasPassword = outputFile = outputFormat = outputConfig = ""

    for parmKey in parmDict.keys():
        l.debug("parmKey: '%s'; parmValue: '%s'" %
                (parmKey, parmDict[parmKey]))
        if (parmKey == "help"):
            printUsage(scriptName)
            sys.exit(0)
        elif (parmKey == "xml"):
            if (parmDict[parmKey] == None):
                raise Exception, "Parameter -x|--xml requires a value ..."
            else:
                xml = parmDict[parmKey]
        elif (parmKey == "json"):
            if (parmDict[parmKey] == None):
                raise Exception, "Parameter -j|--json requires a value ..."
            else:
                jsonFile = parmDict[parmKey]
        elif (parmKey == "cell"):
            l.debug("cell name provided is: '%s'" % (parmDict[parmKey]))
        elif (parmKey == "noempty"):
            if (parmDict[parmKey] == True):
                l.debug("Empty values will be removed ...")
        elif (parmKey == "replace"):
            if (parmDict[parmKey] == True):
                l.debug("Existing JSON file will be replaced if it exists ...")
            replaceJson = parmDict[parmKey]
        elif (parmKey == "influxUrl"):
            if (parmDict[parmKey] == None):
                raise Exception, "Parameter -i|--influxUrl requires a value ..."
            else:
                influxUrl = parmDict[parmKey]
        elif (parmKey == "influxDb"):
            if (parmDict[parmKey] == None):
                raise Exception, "Parameter -d|--influxDb requires a value ..."
            else:
                influxDb = parmDict[parmKey]
        elif (parmKey == "url"):
            if (parmDict[parmKey] == None):
                raise Exception, "Parameter -u|--url requires a value ..."
            else:
                url = parmDict[parmKey]
        elif (parmKey == "omitSummary"):
            if (parmDict[parmKey] == True):
                l.debug("Summary statistics will be omitted ...")
        elif (parmKey == "seconds"):
            if (parmDict[parmKey] == None):
                raise Exception, "Parameter -s|--seconds requires a value ..."
            else:
                seconds = parmDict[parmKey]
        elif (parmKey == "user"):
            if (parmDict[parmKey] == None):
                raise Exception, "Parameter -U|--targetUser requires a value ..."
            else:
                targetUser = parmDict[parmKey]
        elif (parmKey == "password"):
            if (parmDict[parmKey] == None):
                raise Exception, "Parameter -P|--targetPwd requires a value ..."
            else:
                targetPwd = parmDict[parmKey]
        elif (parmKey == "wasUser"):
            if (parmDict[parmKey] == None):
                raise Exception, "Parameter --wasUser requires a value ..."
            else:
                wasUser = parmDict[parmKey]
        elif (parmKey == "wasPassword"):
            if (parmDict[parmKey] == None):
                raise Exception, "Parameter --wasPassword requires a value ..."
            else:
                wasPassword = parmDict[parmKey]
        elif (parmKey == "outputFile"):
            if (parmDict[parmKey] == None):
                raise Exception, "Parameter --outputFile requires a value ..."
            else:
                outputFile = parmDict[parmKey]
        elif (parmKey == "outputFormat"):
            if (parmDict[parmKey] == None):
                raise Exception, "Parameter --outputFormat requires a value ..."
            else:
                outputFormat = parmDict[parmKey]
        elif (parmKey == "outputConfig"):
            if (parmDict[parmKey] == None):
                raise Exception, "Parameter --outputConfig requires a value ..."
            else:
                outputConfig = parmDict[parmKey]
        else:
            l.error("Unsupported option '%s' provided. Exiting ..." % (parmKey))
            sys.exit(1)
    ##
    ## If we get an outputFile/Format:
    if outputFile:
        pass
    ##
    ## outputConfig file must exist
    if outputConfig:
        if not os.path.isfile(outputConfig):
            raise Exception, 'Output config file "%s" does not exist' % outputConfig

    if outputFormat:
        OUTPUT_FORMAT_LIST = ["SPLUNK", "JSON", "DUMMY"]
        if outputFormat.upper() not in OUTPUT_FORMAT_LIST:
            raise Exception, 'output format must be on of: %s' % OUTPUT_FORMAT_LIST
    ##
    ## If we have an xml input file it must exist and be readable
    if (xml != ""):
        ##
        ## XML file must exist. i.e. we need to be able to read the xml file!
        if (not os.path.isfile(xml)):
            raise Exception, 'XML file specified does not exist'
        ##
        ## Can we open the XML file for read?
        try:
            inFile = open(xml, "rU")
            inFile.close()
        except IOError:
            raise Exception, 'XML file can not be read. Check file permissions'
    if (jsonFile != ""):
        ##
        ## JSON file must not exist unless --replace is specified.
        if (os.path.isfile(jsonFile)):
            if (replaceJson != True):
                raise Exception, 'JSON file exists and --replace was not specified'
        ##
        ## Can we open the JSON file for write?
        try:
            ##
            ## We build a temporary file name to test if we can create a file at the location provided
            tmpFileName = jsonFile + ".tmp"
            inFile = open(tmpFileName, "w")
            ##
            ## Cleanup the temporary file
            inFile.close()
            os.remove(tmpFileName)
        except IOError:
            raise Exception, 'JSON file can not be created. Check file permissions'
    ##
    ## --url and --xml are mutual exclusive
    if (((url != "") and (xml != "")) or ((url == "") and (xml == ""))):
        raise Exception, "--xml and --url are mutual exclusive but one is required"
    ##
    ## If we get an url we need an interval in seconds as well
    if ((url != "") and (parmDict["seconds"] == None)):
        raise Exception, "Specifying an url requires to specify an interval in seconds as well"
    ##
    ## If an interval in seconds is provided it must be an integer
    if (parmDict.get("seconds") != None):
        if (not isinstance(parmDict["seconds"], IntType)):
            raise Exception, 'seconds must be an integer'
    ##
    ## If influxUrl is specificied we need also influxDb and vice versa
    if ((influxUrl != "") and ((influxDb == None) or (influxDb == ""))) or ((influxDb != "") and ((influxUrl == None) or (influxUrl == ""))):
        raise Exception, 'influxUrl and influxDb must be specified together'
    ##
    ## If we have a user we need a password and vice versa
    if ((targetUser != "") and ((targetPwd == None) or (targetPwd == ""))) or ((targetUser != "") and ((targetUser == None) or (targetUser == ""))):
        raise Exception, 'targetUser and targetPwd must be specified together'
    ##
    ## If we have a wasUser we need a wasPassword as well and vice versa
    if ((wasUser != "") and ((wasPassword == None) or (wasPassword == ""))) or ((wasPassword != "") and ((wasUser == None) or (wasUser == ""))):
        raise Exception, 'wasUser and wasPassword must be specified together'
    ##
    ## Validata influxDb URL if provided
    if (influxUrl != ""):
        ##
        ## If we have an influxUrl let's check if we can get a ping request
        try:
            (urlSchema, urlHost, urlPort) = splitHttpUrlString(influxUrl)
        except Exception as e:
            raise Exception, sys.exc_info()[1]

        httpConn = getHttpConnection(urlSchema, urlHost, urlPort)
        try:
            tmpUri = "/ping"
            tmpUri += buildQueryString(u=targetUser, p=targetPwd)
            l.debug("Uri to /ping Influx: '%s'" % (tmpUri))
            httpConn.request("GET", tmpUri)
            httpResponse = httpConn.getresponse()
            httpConn.close()
        except NameError as e1:
            errorString = "Failed to verify ping from influx, '%s'" % (
                str(e1))
            raise Exception, errorString
        except Exception as e2:
            errorString = "Failed to get ping from influx, '%s'" % (
                e2.strerror)
            raise Exception, errorString
        ##
        ## indluxDb ping returns code 204
        if (httpResponse.status != httplib.NO_CONTENT):
            httpConn.close()
            ##
            ## If authentication is required
            if (httpResponse.status == httplib.UNAUTHORIZED):
                raise Exception, 'influx database requires authentication'
            else:
                raise Exception, 'influxUrl is incorrect or influx db is not running'
        else:
            l.debug("influx URL ping returned status code: '%d'",
                    httpResponse.status)
        ##
        ## Check if the database exists
        tmpUri = "/query"
        tmpUri += buildQueryString(u=targetUser,
                                   p=targetPwd, q="show databases")
        l.debug("Uri to /query to check for databases: '%s'" % (tmpUri))
        httpConn.request("GET", tmpUri)
        httpResponse = httpConn.getresponse()
        ##
        ## Get the response json
        responseData = httpResponse.read()
        l.debug("influx DB query databases: '%s'" % (str(responseData)))
        httpConn.close()
        influxDebugVarsDict = json.loads(responseData)
        ##
        ## {"results":[{"statement_id":0,"series":[{"name":"databases","columns":["name"],"values":[["pmidata"],["_internal"],["hhuedb"]]}]}]}
        influxSeriesResultList = influxDebugVarsDict["results"]
        for influxSeriesResult in influxSeriesResultList:
            if (influxSeriesResult.get("series") != None):
                influxSeriesDictList = influxSeriesResult["series"]
                l.debug("influxSeriesDictList: '%s'" %
                        (str(influxSeriesDictList)))
                for influxSeriesDict in influxSeriesDictList:
                    l.debug("influxSeriesDict: '%s'" % (str(influxSeriesDict)))
                    if (influxSeriesDict.get("name") == "databases"):
                        databaseSeriesDbList = influxSeriesDict["values"]
                        l.debug("databaseSeriesDbList: '%s'" %
                                (str(databaseSeriesDbList)))
                        validDb = False
                        for databaseSeriesDb in databaseSeriesDbList:
                            if (influxDb in databaseSeriesDb):
                                validDb = True
                        if (validDb != True):
                            raise Exception, 'influxDb not found at influxUrl'



@l.logEntryExit
def parmDictToTuple(parmDict):
    '''
    Parameter dictonary to variable tuple
    '''
    ##
    ## Key values for the parameters dictonary
    parmKeyList = ["help", "xml", "json", "cell", "noempty", "replace", "influxUrl",
                   "influxDb", "omitSummary", "url", "seconds", "user", "password", "wasUser", "wasPassword", "outputFile", "outputFormat", "outputConfig"]
    ##
    ## Copy the parameter values to the variables
    for key in parmKeyList:
        if (key == "xml"):
            if (parmDict.get(key) != None):
                parmServletXmlFile = parmDict[key]
            else:
                parmServletXmlFile = None
            l.debug("XMLFile=%s" % (parmServletXmlFile))
        elif (key == "url"):
            if (parmDict.get(key) != None):
                parmPerfServletUrl = parmDict[key]
            else:
                parmPerfServletUrl = None
            l.debug("PerfServletUrl=%s" % (parmPerfServletUrl))
        elif (key == "json"):
            if (parmDict.get(key) != None):
                parmJsonOutFileName = parmDict[key]
            else:
                parmJsonOutFileName = None
            l.debug("jsonOutFile=%s" % (parmJsonOutFileName))
        elif (key == "cell"):
            parmWasCellName = parmDict[key]
            l.debug("CellName=%s" % (parmWasCellName))
        elif (key == "noempty"):
            parmNoEmpty = parmDict[key]
            l.debug("noempty=%s" % (parmNoEmpty))
        elif (key == "replace"):
            parmReplace = parmDict[key]
            l.debug("replace=%s" % (parmReplace))
        elif (key == "omitSummary"):
            parmOmitSummary = parmDict[key]
            l.debug("omitSummary=%s" % (parmOmitSummary))
        elif (key == "influxUrl"):
            if (parmDict.get(key) != None):
                parmInfluxUrl = parmDict[key]
            else:
                parmInfluxUrl = None
            l.debug("influxUrl=%s" % (parmInfluxUrl))
        elif (key == "influxDb"):
            if (parmDict.get(key) != None):
                parmInfluxDb = parmDict[key]
            else:
                parmInfluxDb = None
            l.debug("influxDb=%s" % (parmInfluxDb))
        elif (key == "seconds"):
            if (parmDict.get(key) != None):
                parmSeconds = parmDict[key]
            else:
                parmSeconds = None
            l.debug("parmSeconds=%s" % (parmSeconds))
        elif (key == "user"):
            if (parmDict.get(key) != None):
                parmTargetUser = parmDict[key]
            else:
                parmTargetUser = None
            l.debug("parmTargetUser=%s" % (parmTargetUser))
        elif (key == "password"):
            if (parmDict.get(key) != None):
                parmTargetPwd = parmDict[key]
            else:
                parmTargetPwd = None
            l.debug("parmTargetPwd=%s" % (parmTargetPwd))
        elif (key == "wasUser"):
            if (parmDict.get(key) != None):
                parmWasUser = parmDict[key]
            else:
                parmWasUser = None
            l.debug("parmWasUser=%s" % (parmWasUser))
        elif (key == "wasPassword"):
            if (parmDict.get(key) != None):
                parmWasPwd = parmDict[key]
            else:
                parmWasPwd = None
            l.debug("parmWasPwd=%s" % (parmWasPwd))
        elif (key == "outputFile"):
            if (parmDict.get(key) != None):
                parmOutfile = parmDict[key]
            else:
                parmOutfile = None
            l.debug("parmOutfile=%s" % (parmOutfile))
        elif (key == "outputFormat"):
            if (parmDict.get(key) != None):
                parmOutFormat = parmDict[key]
            else:
                parmOutFormat = None
            l.debug("parmOutFormat=%s" % (parmOutFormat))
        elif (key == "outputConfig"):
            if (parmDict.get(key) != None):
                parmOutConfig = parmDict[key]
            else:
                parmOutConfig = None
            l.debug("parmOutConfig=%s" % (parmOutConfig))
        else:
            pass
    ##
    ## Return the variables

    return (parmServletXmlFile, parmPerfServletUrl, parmJsonOutFileName, parmWasCellName, parmNoEmpty, parmReplace, parmOmitSummary, parmInfluxUrl, parmInfluxDb, parmSeconds, parmTargetUser, parmTargetPwd, parmWasUser, parmWasPwd, parmOutfile, parmOutFormat, parmOutConfig)
##
## Globals
HTTP_SCHEMA = "http"
HTTPS_SCHEMA = "https"
