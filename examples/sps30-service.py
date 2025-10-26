#!/usr/bin/env python3

import sys
import json
import urllib.request
import urllib.error
from typing import Any
from datetime import datetime, timezone
from sps30 import SPS30
import argparse
import time
import signal
import logging


logging.basicConfig(format='[%(levelname)s] %(asctime)s %(message)s', level=logging.INFO)


parser = argparse.ArgumentParser(description="SPS30 measument tool")
parser.add_argument("--host", type=str, required=True, help="The host of api backend, like: 192.168.0.104:4001")
parser.add_argument("--delay", default=10, type=int, required=False, help="Delay in seconds, default: 10")
opts = parser.parse_args()


logger = logging.getLogger("sps30")


def upload(host: str, d: dict[str, Any]):
    url = "http://" + host + "/api/measurements"
    json_data = json.dumps(d).encode("utf-8")
    req = urllib.request.Request(url, data=json_data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            logger.info(f"Upload succeeded: {response.status} {response.reason}")
    except urllib.error.HTTPError as e:  # HTTP-level errors (e.g., 404, 500)
        json_str = json.dumps(d, ensure_ascii=False, indent=2)
        logger.error(f"HTTPError: {e.code} {e.reason} \n{json_str}")
    except urllib.error.URLError as e:  # Connection problems, refused, etc.
        logger.error(f"URLError: {e.reason}")
    except Exception as e:  # Any other unexpected issue
        logger.exception(f"Unexpected error: {e}")


def map_measurements_to_request(data: dict[str, Any]) -> dict[str, Any]:
    sensor_data = data.get("sensor_data", {})
    timestamp = data.get("timestamp")

    if timestamp is not None:
        iso_timestamp = (
            datetime.fromtimestamp(timestamp, tz=timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        )
    else:
        return {}

    result = {"timestamp": iso_timestamp, "values": []}

    if "mass_density" in sensor_data and "mass_density_unit" in sensor_data:
        for param, value in sensor_data["mass_density"].items():
            result["values"].append({
                "sensor": "mass_density",
                "parameter": param,
                "value": value,
                "unit": sensor_data["mass_density_unit"]
            })

    if "particle_count" in sensor_data and "particle_count_unit" in sensor_data:
        for param, value in sensor_data["particle_count"].items():
            result["values"].append({
                "sensor": "particle_count",
                "parameter": param,
                "value": value,
                "unit": sensor_data["particle_count_unit"]
            })

    if "particle_size" in sensor_data and "particle_size_unit" in sensor_data:
        result["values"].append({
            "sensor": "particle_size",
            "value": sensor_data["particle_size"],
            "unit": sensor_data["particle_size_unit"]
        })

    return result


pm_sensor = SPS30()
def run(host, delay):
    res = pm_sensor.write_auto_cleaning_interval_days(2)
    if res["ok"]:
        print(f"Set auto cleaning interval: {res['value']}s")
    else:
        print(f"Failed to set auto cleaning interval: {res['error']}")

    pm_sensor.start_measurement()
    while True:
        try:
            measurements = pm_sensor.get_measurement()
            if len(measurements) == 0:
                continue

            request_data = map_measurements_to_request(measurements)
            if not request_data:
                continue

            upload(host, measurements)
        except KeyboardInterrupt:
            print("Exiting ...")
            cleanup()
            sys.exit(0)
        finally:
            time.sleep(delay)


def cleanup():
    print("Stop SPS30 sensor hardware safely...")
    pm_sensor.stop_measurement()
    time.sleep(2)
    print("Stop SPS30 sensor complete.")


def signal_handler(signum, frame):
    print(f"Received signal {signum}, stopping service...")
    cleanup()
    sys.exit(0)


signal.signal(signal.SIGTERM, signal_handler)  # Handle systemd stop/restart
signal.signal(signal.SIGINT, signal_handler)   # Handle manual CTRL+C


def main():
    run(opts.host, opts.delay)


if __name__ == "__main__":
    main()
