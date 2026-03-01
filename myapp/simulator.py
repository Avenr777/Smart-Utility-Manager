import random
import math
import time
from datetime import datetime

from .models import Asset, PowerReading


# -------------------------------------------------
# BASE CHARACTERISTICS PER ASSET
# -------------------------------------------------

ASSET_CONFIG = {
    "transformer_block_a": {
        "power_w": 40000,
        "voltage": 415,
    },
    "lab_db_floor1": {
        "power_w": 12000,
        "voltage": 415,
    },
    "ac_unit_lab_1": {
        "power_w": 18000,
        "voltage": 230,
    },
    "streetlight_grid": {
        "power_w": 9000,
        "voltage": 230,
    },
    "transformer_block_b": {
        "power_w": 25000,
        "voltage": 415,
    },
    "hostel_db_a": {
        "power_w": 15000,
        "voltage": 415,
    },
}

READING_TYPES = [
    "power_w",
    "voltage",
    "current_a",
    "energy_kwh",
    "power_factor"
]

# -------------------------------------------------
# GLOBAL CASCADE STATE
# -------------------------------------------------

cascade_state = {
    "active": False,
    "stage": 0,
    "trigger_time": None
}


# -------------------------------------------------
# ENVIRONMENT BEHAVIOR
# -------------------------------------------------

def daily_cycle_multiplier(hour):
    return 1 + 0.3 * math.sin((hour - 6) * math.pi / 12)


def weekend_adjustment(day_of_week):
    return 0.85 if day_of_week >= 5 else 1.0


# -------------------------------------------------
# CASCADE LOGIC
# -------------------------------------------------

def start_cascade():
    cascade_state["active"] = True
    cascade_state["stage"] = 0
    cascade_state["trigger_time"] = datetime.now()


def update_cascade():
    if not cascade_state["active"]:
        return

    elapsed = (datetime.now() - cascade_state["trigger_time"]).seconds
    cascade_state["stage"] = elapsed // 20

    if cascade_state["stage"] > 3:
        cascade_state["active"] = False


def maybe_trigger_failure(asset_name):
    if asset_name == "transformer_block_a":
        if random.random() < 0.02 and not cascade_state["active"]:
            start_cascade()


def apply_cascade(asset_name, value, reading_type):
    if not cascade_state["active"]:
        return value

    stage = cascade_state["stage"]

    if stage >= 0 and asset_name == "transformer_block_a":
        return value * random.uniform(1.5, 2.2)

    if stage >= 1 and asset_name == "lab_db_floor1":
        return value * random.uniform(1.3, 1.7)

    if stage >= 2 and asset_name == "hostel_db_a":
        return value * random.uniform(1.2, 1.5)

    return value


# -------------------------------------------------
# SENSOR SIMULATION
# -------------------------------------------------

def simulate_power(asset_name, base_power):
    now = datetime.now()
    cycle = daily_cycle_multiplier(now.hour)
    weekend_factor = weekend_adjustment(now.weekday())
    noise = random.uniform(-0.05, 0.05)

    value = base_power * cycle * weekend_factor * (1 + noise)
    return round(value, 2)


def simulate_voltage(base_voltage):
    noise = random.uniform(-0.02, 0.02)
    return round(base_voltage * (1 + noise), 2)


def simulate_current(power_w, voltage):
    # I = P / V
    current = power_w / max(voltage, 1)
    noise = random.uniform(-0.05, 0.05)
    return round(current * (1 + noise), 2)


def simulate_power_factor():
    return round(random.uniform(0.85, 0.99), 3)


# -------------------------------------------------
# MAIN GENERATION
# -------------------------------------------------

def generate_all_assets():

    for asset_name, config in ASSET_CONFIG.items():

        asset_obj, _ = Asset.objects.get_or_create(name=asset_name)

        base_power = config["power_w"]
        base_voltage = config["voltage"]

        # Possibly trigger cascade
        maybe_trigger_failure(asset_name)

        update_cascade()

        # 1️⃣ POWER
        power = simulate_power(asset_name, base_power)
        power = apply_cascade(asset_name, power, "power_w")

        # 2️⃣ VOLTAGE
        voltage = simulate_voltage(base_voltage)
        voltage = apply_cascade(asset_name, voltage, "voltage")

        # 3️⃣ CURRENT
        current = simulate_current(power, voltage)

        # 4️⃣ ENERGY (incremental accumulation)
        last_energy = PowerReading.objects.filter(
            asset=asset_obj,
            reading_type="energy_kwh"
        ).order_by("-timestamp").first()

        if last_energy:
            energy = last_energy.value + (power / 1000) * (5 / 3600)
        else:
            energy = (power / 1000) * (5 / 3600)

        energy = round(energy, 4)

        # 5️⃣ POWER FACTOR
        pf = simulate_power_factor()

        readings = {
            "power_w": power,
            "voltage": voltage,
            "current_a": current,
            "energy_kwh": energy,
            "power_factor": pf
        }

        for reading_type, value in readings.items():
            PowerReading.objects.create(
                asset=asset_obj,
                reading_type=reading_type,
                value=value
            )


# -------------------------------------------------
# LOOP MODE
# -------------------------------------------------

if __name__ == "__main__":
    while True:
        generate_all_assets()
        print("Generated readings at", datetime.now())
        time.sleep(5)