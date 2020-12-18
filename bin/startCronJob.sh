#!/usr/bin/env bash

## Set default loglevel 
export TWOI_LOG_LEVEL=${TWOI_LOG_LEVEL:-INFO}


## Call data collector
##### ./was-metrics-exporter.py -u "https://wp04.hhue.at:10042/wasPerfTool/servlet/perfservlet?node=wp04Node&server=WebSphere_Portal&module=connectionPoolModule+threadPoolModule+jvmRuntimeModule" -j /dev/shm/hhue.json -r -n -o -i http://localhost:8086 -d pmidata -U admin -P start123. -s 5 --wasUser wpadmin --wasPassword start123. --outputConfig ./whitelist.config > /2tmp/cvtPmiDta_$(date +"%Y%m%d_%H%M%S").log 2>&1
##### ./was-metrics-exporter.py -u "https://wp04.hhue.at:10042/wasPerfTool/servlet/perfservlet?module=connectionPoolModule+threadPoolModule+jvmRuntimeModule" -j /dev/shm/hhue.json -r -n -o -i http://localhost:8086 -d pmidata -U admin -P start123. -s 5 --wasUser wpadmin --wasPassword start123. --outputConfig ./whitelist.config > /2tmp/cvtPmiDta_$(date +"%Y%m%d_%H%M%S").log 2>&1
##### ./was-metrics-exporter.py -u "https://wp04.hhue.at:10042/wasPerfTool/servlet/perfservlet?module=connectionPoolModule+threadPoolModule+jvmRuntimeModule" -j /dev/shm/hhue.json -r -n -o -i http://localhost:8086 -d pmidata -U admin -P start123. -s 5 --wasUser wpadmin --wasPassword start123. > /2tmp/cvtPmiDta_$(date +"%Y%m%d_%H%M%S").log 2>&1

./was-metrics-exporter.py \
  -u "https://wp04.hhue.at:10042/wasPerfTool/servlet/perfservlet" \
  --wasUser wpadmin --wasPassword start123.  \
  --outputConfig ./whitelist.config \
  -j /dev/shm/hhue.json -r -n -o \
  -s 5 \
  -i http://localhost:8086 -d pmidata -U admin -P start123. \
   > /2tmp/cvtPmiDta_$(date +"%Y%m%d_%H%M%S").log 2>&1

##
## Done ...
rc=$?
echo "Finished processing at $(date) with rc: ${rc}"
