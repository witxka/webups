#!/usr/bin/env python3
# encoding: utf-8

# Description  : Read tecnair conditioner sensors through modbus and ouput it as JSON.
#                Sensors are given with csv file. The output with check_mk header.
#                The script use agent_modbus cpp application.
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

def get_info(sensors, scope, tecnairIP):
    """Get sensors values from tecnair conditioner through modbus over IP and output them as JSON.

    @param sensors   The dictionary of sensors to read and format output.
    @param scope     The scope for sensor parameters.
    @param tecnairIP The IP address for tecnair conditioner to connect to modbus over IP.
    @return The dictionary for sensors values with their parameters.
    """

    infoFor = {}
    info = {}
    info["Adapter"] = "parameters"
    outputDict = {}

    webupsInfo = subprocess.check_output(["curl","-s","http://" + tecnairIP +
        "/cgi-bin/realInfo.cgi"])
    webupsParams = webupsInfo.splitlines()

    for sensor in sensors:
      sensorDict = {}
      print(strToFloat(webupsParams[int(sensor["position"])]))
      print(strToFloat(sensor["multiply"]))
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
  """Main function. Read sensors for tecnair conditioner and 
    output them as JSON.
    
  @param argv[1] The IP address for tecnair conditioner.
  @param argv[2] The csv file with tecnair sensors to check.
  @param argv[3:] Additional csv files with tecnair sensors to check.
  @return The output in JSON format.
  """

  try:
    # add param checking
    if (len(sys.argv) < 3):
      print("Usage: {0} IP sensors1.csv [...] ".format(sys.argv[0]))
      print("  IP: The IP address for modbus over IP for tecnair conditioner")
      print("  sensors1.csv: The csv file with tenair modbus sensors to check")
      print("  ...: Additionals csv files with tenair modbus sensors to check")
      sys.exit(0)

    tecnairIP = sys.argv[1]
    info = {}
    for i in range(2,len(sys.argv)):
      sensors = read_csv(sys.argv[i])
      scope = sys.argv[i].split(".")[0]
      info.update(get_info(sensors, scope, tecnairIP).items());
    print(json.dumps(info))
  except Exception as e:
    logging.error(traceback.format_exc())

if __name__ == "__main__":
    main()
