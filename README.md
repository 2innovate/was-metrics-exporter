# was-metrics-exporter

## Motivation
Retrieving traditional WebSphere Application Server (tWAS) performance data (PMI) via the MBeans is not trivial: the MBeans providing performance data are quite complex and therefore can't be retrieved using standard tools like e.g. [Jolokia](https://jolokia.org/).  
As an alternative way to retrieve PMI data, tWAS ships with a [Performance Servlet](https://www.ibm.com/support/knowledgecenter/SSEQTP_8.5.5/com.ibm.websphere.base.doc/ae/tprf_devprfservlet.html)-EAR which provides PMI data obtained from the runtime as XML data. A major drawback of performance servlet is that nowadays most modern metrics aggregation tools work with Json or plain text inputs (like [InfluxDb](https://www.influxdata.com/)) and don't support (complex) XML input directly.  

The idea of this project is to provide a tool to fetch and transform PMI data from XML into multiple target formats. Additional output formats can easily be introduced by writing a new output plugin. 

### Inputs
`was-metrics-exporter` can read the XML data from either:
- an URL from which the XML PMI data can be fetched; usually that would be the URL of WAS performance servlet.  
  This option allows to continuously retrieve PMI data at a specified interval.
- a file to which the performance servlet data was previously exported to 
  (mainly used for debugging offline without a running WAS server)

### Outputs
Currently we are supporting the following XML data conversions:
- Output to a JSON file (complete output of the performance servlet data in JSON format)
- Direct output to InfluxDb via REST API if proper InfluxDb parameters are passed
- Output to a text-file that is easy to parse by a Splunk collector (key=value pairs)

### Output configuration (white-listing metrics)
While the JSON file output always contains the full performance servlet PMI data, the output for Influx DB and Splunk can be granuarly configured to output only specific values for selected metrics. This allows to reduce the output to the minimum.  
#### Note:
Although white-listing allows you to reduce the output data, it is far better and highly recommeded to request only the required data from the performance servlet in the first place by [specifying the proper parameters when invoking the servlet](https://www.ibm.com/support/knowledgecenter/SSEQTP_9.0.5/com.ibm.websphere.base.doc/ae/cprf_servletinput.html)!

A *white-list configuration* is being processed based on the *j2eetype* with the following rules:
- If no values are defined for a *j2eetype*, then *all* values will be added to the output.
- If a *j2eetype* is not defined in the config file, no values will be added to the output.
- if a *j2eetype* is defined in the config file and specific values are configured, then only these values will be added

A sample [while-list](bin/whitelist.config) configuration file can be found in the scripts directory.


### Invoking the script
`was-metrics-exporter` requires Python 2.7 and can be invoked using the following parameters:
```

    Usage: was-metrics-exporter.py [ --help (this information) ]

                        [ --xml |-x <perfServletXmlFile>
                        [ --url |-u <perfServletUrl>  [--seconds|-s <seconds>] [--wasUser <was_user> --wasPassword <wasPassword>] ]
                        [ --cell|-c <was_cell_name>]

                        [ --json|-j <json_outfile>]
                        [ --noempty|-n]  [--omitSummary|-o ]

                        [ --influxUrl|-i <url> --influxDb|-d <dbName>]  [-U|--targetUser <user> -P|--targetPwd <password> ]

                        [ --outputFile <file-name> ]
                        [ --outputFormat  { "INFLUX" | "SPLUNK" | "DUMMY" } ]
                        [ --replace|-r ]
                        [ --outputConfig <whitelist-config filename> ]

    whereby:
        --xml |-x              name of the file containing WAS performance servlet output. Mutual exclusive with --url.
        --url | -u             full URL of the performance servlet to get the data. For example:
                                    http://<host>:<port>/wasPerfTool/servlet/perfservlet?node=<nodeName>&server=<serverName>&module=connectionPoolModule+jvmRuntimeModule
        --seconds | -s         interval in seconds for fetching <perfServletUrl>
        --json    | -j         filename for JSON output. Use for simple XML-2-JSON conversion.

    optional:
        --cell        | -c     name of the WAS cell being used as the root of all tags. Defaults to: "cell"
        --noempty     | -n     remove empty metrics. Defaults to false
        --replace     | -r     replace the <json_outfile> if the file exists. Defaults to false
        --omitSummary | -o     omit summary measurement like for example measurement for JDBC providers

        --influxUrl   | -i     rest URL for InfluxDb to which data should be posted
        --influxDb    | -d     influxDb database to which data should be posted. You might attach a retention policy like:
                                  "CREATE RETENTION POLICY TWO_WEEKS ON pmidata DURATION 2w REPLICATION 1"
        --targetUser  | -U     user name to authenticate on the target platform (for example influxDb)
        --targetPwd   | -P     password being used to authenticate on the target platform (for example influxDb)

        --wasUser              user name to authenticate against WebSphere to retrieve the performance servlet data
        --wasPassword          password to authenticate against WebSphere to retrieve the performance servlet data

        --outputFile           output filename
        --outputFormat         valid formats; "INFLUX", "SPLUNK", "DUMMY"
        --outputConfig         configuration filename to configure output columns ( eg. whitelist.config )
```

## Get Involved

Please open an issue to discuss your problem/feature/enhancement, and reference that issue in your pull request! 

## Authors

`was-metrics-exporter` was created by 
- `Hermann Huebler <hhuebler@2innovate.at>` and
- `Thomas Hikade <thikade@2innovate.at>`   

sponsored by [2innovate IT Consulting GmbH](https://2innovate.at).

<img src="https://2innovate.at/images/header-logo.svg" width="200"><br/><br/>

## License

GNU General Public License v3.0 or later

See [COPYING](COPYING) to see the full text.