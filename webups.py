from .agent_based_api.v1 import *
import json
import enum


class SensorType(enum.Enum):
    TEMP = "temp"
    IN = "in"
    FAN = "fan"
    CPU = "cpu"
    POWER = "power"
    CURR = "curr"
    ENERGY = "energy"
    INTRUSION = "intrusion"
    HUMIDITY = "humidity"
    HOURS = "hours"


class Sensor:
    def __init__(self):
        self.name = None
        self.sensor_type = None
        self.value = None
        self.crit_value = None
        self.warn_value = None


class Chip:
    def __init__(self):
        self.name = None
        self.adapter = None
        self.sensors = []


def str_to_float(str_val):
    try:
        return float(str_val)
    except ValueError as e:
        return None


def parse_webups(string_table):
    json_str = ""
    for line in string_table:
        for word in line:
            json_str += word
            json_str += " "
        json_str += "\n"

    sensors = json.loads(json_str)

    parsed_sensors = []

    for chip_name in sensors:
        parsed = Chip()
        parsed.adapter = sensors[chip_name]["Adapter"]

        for sensor_name in sensors[chip_name]:
            if sensor_name == "Adapter":
                continue
            sensor = Sensor()
            sensor.name = sensor_name
            for sensor_val_name in sensors[chip_name][sensor_name]:
                if sensor_val_name.endswith("_input"):
                    sensor.value = str_to_float(sensors[chip_name][sensor_name][sensor_val_name])
                    for stype in SensorType:
                        if sensor_val_name.startswith(stype.value):
                            sensor.sensor_type = stype
                    if sensor.sensor_type == None:
                        print("unknown sensor type")

                if sensor_val_name.endswith("crit"):
                    sensor.crit_value = str_to_float(sensors[chip_name][sensor_name][sensor_val_name])

                if sensor_val_name.endswith("max"):
                    sensor.warn_value = str_to_float(sensors[chip_name][sensor_name][sensor_val_name])

            parsed.sensors.append(sensor)

        parsed_sensors.append(parsed)

    return parsed_sensors


def _discover_webups(section, sensor_type):
    for chip in section:
        for sensor in chip.sensors:
            if sensor.sensor_type != sensor_type:
                continue
            service_name = chip.adapter + " " + sensor.name
            yield Service(item=service_name)


def check_webups(item, params, section, levels_upper_key, levels_lower_key, metric_name):
    for chip in section:
        for sensor in chip.sensors:
            service_name = chip.adapter + " " + sensor.name
            if service_name == item:
                if sensor.value != None:
                    levels_lower = None
                    levels_upper = None

                    if params != {}:
                        # rule exists
                        if levels_upper_key in params:
                            levels_upper = params[levels_upper_key]
                        if levels_lower_key in params:
                            levels_lower = params[levels_lower_key]
                    elif sensor.crit_value != None or sensor.warn_value != None:
                        # no rules set use values from lm-sensors output
                        if sensor.crit_value == None:
                            sensor.crit_value = sensor.warn_value
                        elif sensor.warn_value == None:
                            sensor.warn_value = sensor.crit_value

                        levels_upper = (sensor.warn_value, sensor.crit_value)
                    elif sensor.warn_value == None and sensor.crit_value == None:
                        yield Result(state=State.OK, summary="Always Ok")
                        yield Metric(metric_name, sensor.value)
                        return

                    result, metric = check_levels(
                        sensor.value,
                        levels_lower=levels_lower,
                        levels_upper=levels_upper,
                        metric_name=metric_name,
                    )

                    yield metric
                    yield result
                else:
                    yield Result(state=State.WARN, summary="No input delivered by sensors command")
                return


def check_webups_temp(item, params, section):
    if "trend_compute" in params:
        raise Exception("trend_compute is not supported by webups plugin")

    if "device_levels_handling" in params:
        raise Exception("device_levels_handling not supported, webups always uses sensor values of no rule is configured")

    if "input_unit" in params:
        raise Exception("input_unit is not supported by webups plugin")

    if "output_unit" in params:
        if params["output_unit"] == "c":
            pass  # is the default anyway
        elif params["output_unit"] == "f":
            for chip in section:
                for sensor in chip.sensors:
                    if sensor.value == None:
                        continue
                    sensor.value = (sensor.value * 1.8) + 32
        elif params["output_unit"] == "k":
            for chip in section:
                for sensor in chip.sensors:
                    if sensor.value == None:
                        continue
                    sensor.value = sensor.value + 273.15

    for r in check_webups(item, params, section, "levels", "levels_lower", "temperature"):
        yield r

def check_webups_hours(item, params, section):
    for r in check_webups(item, params, section, "levels", "levels_lower", "hours"):
        yield r


def check_webups_fan(item, params, section):
    for r in check_webups(item, params, section, "upper", "levels", "fan_speed"):
        yield r


def check_webups_volt(item, params, section):
    for r in check_webups(item, params, section, "levels", "levels_lower", "volt"):
        yield r


def discover_webups_temp(section):
    for service in _discover_webups(section, SensorType.TEMP):
        yield service


def discover_webups_hours(section):
    for service in _discover_webups(section, SensorType.HOURS):
        yield service


def discover_webups_fan(section):
    for service in _discover_webups(section, SensorType.FAN):
        yield service


def discover_webups_volt(section):
    for service in _discover_webups(section, SensorType.IN):
        yield service


register.check_plugin(
    name="webups_temp",
    service_name="webups_temp %s",
    sections=["webups"],
    discovery_function=discover_webups_temp,
    check_function=check_webups_temp,
    check_ruleset_name="temperature",
    check_default_parameters={},
)

register.check_plugin(
    name="webups_hours",
    service_name="webups_hours %s",
    sections=["webups"],
    discovery_function=discover_webups_hours,
    check_function=check_webups_hours,
    check_ruleset_name="hours",
    check_default_parameters={},
)

register.check_plugin(
    name="webups_fan",
    service_name="webups_fan %s",
    sections=["webups"],
    discovery_function=discover_webups_fan,
    check_function=check_webups_fan,
    check_ruleset_name="hw_fans",
    check_default_parameters={},
)

register.check_plugin(
    name="webups_volt",
    service_name="webups_volt %s",
    sections=["webups"],
    discovery_function=discover_webups_volt,
    check_function=check_webups_volt,
    check_ruleset_name="voltage",
    check_default_parameters={},
)

register.agent_section(
    name="webups",
    parse_function=parse_webups,
)
