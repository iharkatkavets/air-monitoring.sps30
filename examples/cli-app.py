import sys
import json
from time import sleep
from sps30 import SPS30


def print_result(name: str, result: dict, unit: str = ""):
    if result.get("ok"):
        suffix = unit if unit else ""
        print(f"{name}: {result['value']}{suffix}")
    else:
        print(f"Failed to read {name.lower()}: {result['error']}")


if __name__ == "__main__":
    pm_sensor = SPS30()

    print_result("Firmware version", pm_sensor.firmware_version())
    print_result("Product type", pm_sensor.product_type())
    print_result("Serial number", pm_sensor.serial_number())
    print_result("Status register", pm_sensor.read_status_register())
    print_result("Auto cleaning interval", pm_sensor.read_auto_cleaning_interval(), "s")

    res = pm_sensor.write_auto_cleaning_interval_days(2)
    if res["ok"]:
        print(f"Set auto cleaning interval: {res['value']}s")
    else:
        print(f"Failed to set auto cleaning interval: {res['error']}")

    pm_sensor.start_measurement()

    while True:
        try:
            print(json.dumps(pm_sensor.get_measurement(), indent=2))
            sleep(2)
        except KeyboardInterrupt:
            print("Stopping measurement...")
            break

    pm_sensor.stop_measurement()
    sys.exit(0)
