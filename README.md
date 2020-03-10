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
- Output to a JSON file
- Output to an InfluxDb using InfluxDb's REST API

### Invoking the script
The script can be invoked using the following parameters:
```
Usage: processPerfServletData.py --help (this information) | [--xml|-x <perfServletXmlFile> | (--url |-u <perfServletUrl> | --seconds|-s <seconds> --wasUser <was_user> --wasPassword <wasPassword>]) [--json|-j <json_outfile>] [--cell|-c <was_cell_name>] [--noempty|-n] [--replace|-r] [--influxUrl|-i <url> --influxDb|-d <dbName>] [--omitSummary|-o [-U|--targetUser <user> -P|--targetPwd <password>]]
    Whereby:
        <perfServletXmlFile>        name of the file with the WAS performance servlet output. Mutual exclusise with <perfServletXmlFile>
        <perfServletUrl>        full URL of the performance servlet to get the data. For example:
                                http://<host>:<port>/wasPerfTool/servlet/perfservlet?node=<nodeName>&server=<serverName>&module=connectionPoolModule+jvmRuntimeModule
        <seconds>               interval in seconds between fetching <perfServletUrl>
        <json_outfile>          name of the file to which the JSON output will be written
optional:
        <was_cell_name>         name of the WAS cell being used as the root of the tags. Defaults to: "cell"
        <--noempty|-n>          remove empty metrics. Defaults to false
        <--replace|-r>          replace the <json_outfile> if the file exists. Defaults to false
        <--omitSummary|-o>      omit summary measurement like for example measurement for JDBC providers
        <--influxUrl|-i>        rest URL for InfluxDb to which data should be posted
        <--influxDb|-d>         influxDb database to which data should be posted
        <--targetUser|-U>       user name to authenticate on the target plattform (for example influxDb)
        <--targetPwd|-d>        password being used to authenticate on the target plattform (for example influxDb)
        <--wasUser>             user name to authenticate against WebSphere to retrieve the performance servlet data
        <--wasPassword>         password o authenticate against WebSphere to retrieve the performance servlet data
```
