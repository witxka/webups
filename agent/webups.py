#!/usr/bin/env python3
# encoding: utf-8

# Description  : Read webups sensors through http and ouput it as JSON.
#                Sensors are given with csv file.
# Author       : witxka@gmail.com 

import subprocess
import json
import sys
import csv
import socket
import logging
import traceback

def strToFloat(strVal):
  try:
    return float(strVal)
  except ValueError as e:
    return None

def get_info(sensors, scope, webupsIP):
    """Get sensors values from webups through curl over http and output them as JSON.

    @param sensors   The dictionary of sensors to read and format output.
    @param scope     The scope for sensor parameters.
    @param webupsIP  The IP address for webups to connect to http.
    @return The dictionary for sensors values with their parameters.
    """

    infoFor = {}
    info = {}
    info["Adapter"] = "parameters"
    outputDict = {}

    webupsInfo = subprocess.check_output(["curl","-s","http://" + webupsIP +
        "/cgi-bin/realInfo.cgi"])
    webupsParams = webupsInfo.splitlines()

    for sensor in sensors:
      sensorDict = {}
      sensorDict[sensor["name"] + "_input"] = round(strToFloat(webupsParams[int(sensor["position"])-1])*strToFloat(sensor["multiply"]),2)
      sensorDict[sensor["name"] + "_max"] = strToFloat(sensor["warn"])
      sensorDict[sensor["name"] + "_crit"] = strToFloat(sensor["crit"])
      sensorDict[sensor["name"] + "_min"] = strToFloat(sensor["min"])
      info[sensor["name"] + ", " + sensor["type"]] = sensorDict
    outputDict["webups"] = info
    return outputDict

def read_csv(filename):
  with open(filename) as f:
    file_data=csv.reader(f)
    headers=next(file_data)
    return [dict(zip(headers,i)) for i in file_data]

def main():
  """Main function. Read sensors for webups and 
    output them as JSON.
    
  @param argv[1] The IP address for webups.
  @param argv[2] The csv file with webups sensors to check.
  @param argv[3:] Additional csv files with webups sensors to check.
  @return The output in JSON format.
  """

  try:
    # add param checking
    if (len(sys.argv) < 3):
      print("Usage: {0} IP sensors1.csv [...] ".format(sys.argv[0]))
      print("  IP: The IP address for http for webups")
      print("  sensors1.csv: The csv file with webups sensors to check")
      print("  ...: Additionals csv files with webups sensors to check")
      sys.exit(0)

    webupsIP = sys.argv[1]
    info = {}
    for i in range(2,len(sys.argv)):
      sensors = read_csv(sys.argv[i])
      scope = sys.argv[i].split(".")[0]
      info.update(get_info(sensors, scope, webupsIP).items());
    print(json.dumps(info))
  except Exception as e:
    logging.error(traceback.format_exc())

if __name__ == "__main__":
    main()
