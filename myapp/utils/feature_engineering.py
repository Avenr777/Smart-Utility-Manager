import pandas as pd
import numpy as np
from datetime import datetime

def build_feature_vector(current_value, previous_value, history_values, reading_type):
    """
    Builds feature vector exactly matching training logic.

    Parameters:
    - current_value: latest sensor value
    - previous_value: previous sensor value
    - history_values: last 6 values (chronological)
    - reading_type: sensor type (voltage, power_w, energy_kwh, etc.)
    """

    now = datetime.now()

    # -----------------------------------
    # Special handling for energy_kwh
    # -----------------------------------
    if reading_type == "energy_kwh":

        # Energy is cumulative — use delta
        delta = current_value - previous_value

        # Compute deltas from history
        deltas = np.diff(history_values)

        rolling_mean_6 = np.mean(deltas)
        rolling_std_6 = np.std(deltas, ddof=1)

        df = pd.DataFrame([{
            "delta": delta,
            "lag_1": previous_value,
            "rolling_mean_6": rolling_mean_6,
            "rolling_std_6": rolling_std_6,
            "hour": now.hour,
            "day_of_week": now.weekday()
        }])

    else:
        # -----------------------------------
        # Standard case for other readings
        # -----------------------------------

        rolling_mean_6 = np.mean(history_values)

        # pandas rolling std default ddof=1
        rolling_std_6 = np.std(history_values, ddof=1)

        df = pd.DataFrame([{
            "value": current_value,
            "lag_1": previous_value,
            "rolling_mean_6": rolling_mean_6,
            "rolling_std_6": rolling_std_6,
            "hour": now.hour,
            "day_of_week": now.weekday()
        }])

    return df