"""
lookup_row.py
=============
Lookup utility for retrieving exact sensor telemetry and true target values for any (EngineID, Cycle) in PS_2_final_dataset.
Outputs ready-to-use curl command for API testing.
"""

import sys
import json
import pandas as pd

from backend.ml.config import DATA_DIR


def lookup(engine_id: int, cycle: int):
    full = pd.read_csv(DATA_DIR / "turbojet_complete_dataset.csv")
    row = full[(full["EngineID"] == engine_id) & (full["Cycle"] == cycle)]

    if row.empty:
        print(f"No row found for EngineID={engine_id}, Cycle={cycle}.")
        print(f"Valid EngineIDs: {sorted(full['EngineID'].unique())}")
        print(f"Valid Cycles: {full['Cycle'].min()}-{full['Cycle'].max()}")
        return

    row = row.iloc[0]

    sensor_fields = [
        "Altitude_m", "Mach", "Tamb_K", "Pamb_Pa",
        "RPM_rev_min", "FuelFlow_kg_s",
        "P2_Pa", "T2_K", "P3_Pa", "T3_K", "P4_Pa", "T4_K",
    ]
    sensor_payload = {
        "EngineID": int(row["EngineID"]),
        "Cycle": int(row["Cycle"]),
    }
    sensor_payload.update({f: float(row[f]) for f in sensor_fields})

    print(f"=== EngineID={engine_id}, Cycle={cycle} ===\n")
    print("Ready-to-paste curl command:\n")
    print(
        "curl -X 'POST' 'http://127.0.0.1:8000/predict' "
        "-H 'accept: application/json' -H 'Content-Type: application/json' "
        f"-d '{json.dumps(sensor_payload)}'"
    )
    print("\n=== ACTUAL ground truth values for THIS EXACT row ===\n")
    for target in ["CompressorHealth", "CombustorHealth", "TurbineHealth",
                    "OverallHealth", "Thrust_N", "TSFC_g_N_s"]:
        print(f"  {target:18s} {row[target]}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 -m backend.ml.lookup_row <EngineID> <Cycle>")
        sys.exit(1)
    lookup(int(sys.argv[1]), int(sys.argv[2]))

