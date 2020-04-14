# cvtPmiDta

## Motivaton
Retrieving traditional WebSphere Application Server (tWAS) performance data (PMI) via the MBeans is not trivial. The MBeans providing the performance data are quite complex and therefore can't be retrieved using standard tools like for example [Jolokia](https://jolokia.org/).
As an alternative to retrieve the PMI data tWAS provides the [performance servlet](https://www.ibm.com/support/knowledgecenter/SSEQTP_8.5.5/com.ibm.websphere.base.doc/ae/tprf_devprfservlet.html) which retrieves the PMI data as provides them as an XML file.
The issue with this approach is that many modern tools to store the data (like for example [InfluxDb](https://www.influxdata.com/)) don't support XML input.
The idea of this project is to provide a tool to convert the XML data retrieved by the performance servlet to multiple target formats.

### Script input
The script can read the XML data from:
- a file to which the performance servlet data was exported before
- an URL from which the XML data can be fetched at runtime. This option allows to retrieve the data in a provided interval.

### Script output
At the time of writing this document we are supporting the following conversations:
- Output to a JSON file (complete output of the performance servlet data in JSON format)
- Output to an InfluxDb using InfluxDb's REST API if proper influx Db parameters are passed
- Output to a file in SPLUNK format

#### Output configuration (white-list)
While the JSON file being created always contains the full performance servlet output data the output for Influx DB and SPLUNK can be configured granuarly to write only specific value for specific metrics. This allows to reduce the output to the minimum. 
Although this white-list function allows to reduce the output it is highly recommeded to request only the minimum of the required data from the performance servlet by [specifying the proper parameters when invoking the servlet](https://www.ibm.com/support/knowledgecenter/SSEQTP_9.0.5/com.ibm.websphere.base.doc/ae/cprf_servletinput.html).

The white-list is being processed based on the j2eetype with the following rules:
- If no values are defined for a j2eetype all values will be added to the output.
- If a j2eetype is not in the config no values will be added to the output.
- if a j2eetype is defined in the file and specific values are conigured only these values will be added

A sample white-list configuration files is attached to the project in the scripts directory (whilelist.config).


### Invoking the script
The script can be invoked using the following parameters:
```
    Usage: processPerfServletData.py [ --help (this information) ]

                        [ --xml |-x <perfServletXmlFile>
                        [ --url |-u <perfServletUrl>  [--seconds|-s <seconds>] [--wasUser <was_user> --wasPassword <wasPassword>] ]
                        [ --cell|-c <was_cell_name>]

                        [ --json|-j <json_outfile>]
                        [--noempty|-n]
                        [--omitSummary|-o ]

                        [--influxUrl|-i <url> --influxDb|-d <dbName>]  [-U|--targetUser <user> -P|--targetPwd <password>]

                        [ --outputFile <file-name> ]
                        [ --outputFormat  { "JSON" | "SPLUNK" | "DUMMY" } ]
                        [ --replace|-r]
                        [ --outputConfig <config-file-name> ]

    whereby:
        <perfServletXmlFile>    name of the file with the WAS performance servlet output. Mutual exclusise with <perfServletXmlFile>"
        <perfServletUrl>        full URL of the performance servlet to get the data. For example:"
                                    http://<host>:<port>/wasPerfTool/servlet/perfservlet?node=<nodeName>&server=<serverName>&module=connectionPoolModule+jvmRuntimeModule"
        <seconds>               interval in seconds between fetching <perfServletUrl>"
        <json_outfile>          name of the file to which the JSON output will be written"

    optional:"
        <was_cell_name>         name of the WAS cell being used as the root of the tags. Defaults to: "cell""
        <--noempty|-n>          remove empty metrics. Defaults to false"
        <--replace|-r>          replace the <json_outfile> if the file exists. Defaults to false"
        <--omitSummary|-o>      omit summary measurement like for example measurement for JDBC providers"
        <--influxUrl|-i>        rest URL for InfluxDb to which data should be posted"
        <--influxDb|-d>         influxDb database to which data should be posted. You might attach a retention policy like: 
                        "CREATE RETENTION POLICY TWO_WEEKS ON pmidata DURATION 2w REPLICATION 1""
        <--targetUser|-U>       user name to authenticate on the target platform (for example influxDb)"
        <--targetPwd|-d>        password being used to authenticate on the target platform (for example influxDb)"
        <--wasUser>             user name to authenticate against WebSphere to retrieve the performance servlet data"
        <--wasPassword>         password to authenticate against WebSphere to retrieve the performance servlet data"
        <--outputFile>          output filename"
        <--outputConfig>        configuration file name to configure output columns"
```
