from pathlib import Path
import numpy as np
import pandas as pd
from .config import RAW_DIR, PROCESSED_DIR, FIGS_DIR, C_CHORD_M
from .io_utils import read_csvs_from_dir, write_csv

# def process_directory(rawt_dir: Path, out_dir: Path):
#   out_dir.mkdir(parents=True, exist_ok=True)
#    dfs = read_csvs_from_dir(rawt_dir)
#   cl_rows = []

    
# Expected CSV headers (exact strings)
H_TEMP_K      = "%Atmospheric Temperature [K]"
H_PATM_PA     = "Atmospheric Pressure [Pa]"
H_RHO_KGM3    = "Atmospheric Density [kg/m^3]"
H_V_MS        = "Airspeed [m/s]"
H_Q_PITOT_PA  = "Pitot Dynamic Pressure [Pa]"
H_Q_AUX_PA    = "Aux Dynamic Pressure [Pa]"
H_VOLTAGE_V   = "Actual Voltage [V]"
H_ALPHA_DEG   = "Angle of Attack [deg]"
H_SPAN_IN     = "Spanwise Position [in]"
H_STING_AX    = "Sting Axial Force [N]"
H_STING_NM    = "Sting Normal Force [N]"
H_STING_PM    = "Sting Pitching Moment [Nm]"
H_ELD_X_MM    = "ELD Probe X-Axis [mm]"
H_ELD_Y_MM    = "ELD Probe Y-Axis [mm]"

# 16 Scanivalve differential pressures (port - test-section static) in Pa
SCAN_COLS = [f"Scanivalve Pressure {i} [Pa]" for i in range(1, 17)]

EXPECTED_COLS = [
    H_TEMP_K, H_PATM_PA, H_RHO_KGM3, H_V_MS,
    H_Q_PITOT_PA, H_Q_AUX_PA, H_VOLTAGE_V, H_ALPHA_DEG,
    H_SPAN_IN, H_STING_AX, H_STING_NM, H_STING_PM,
    H_ELD_X_MM, H_ELD_Y_MM
] + SCAN_COLS

# Geometry file (must be in data/raw/)
GEOM_FILENAME = "port_locations.xlsx"  # columns: port,x_m,y_m,side ('upper'/'lower')





def init_data(raw_dir: Path) -> dict[str, pd.DataFrame]:
    dfs: dict[str, pd.DataFrame] = {}

    for csv_path in sorted(raw_dir.glob("ASEN_2802___WTData_LA_Test_AoA_*.csv")):
        try:
            df = pd.read_csv(csv_path)

            df = df[EXPECTED_COLS]

            key = csv_path.stem
            dfs[key] = df
            print(f"Loaded {csv_path.name} with {len(df)} rows")
        except Exception as e:
            print(f"Skipped {csv_path.name} due to error: {e}") 
    if not dfs:
        print(f"No valid CSV files found in {raw_dir}")
    return dfs

def summarize_means(dfs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for key, df in dfs.items():
        means = df.mean(numeric_only=True)
        q_inf = float(means.get(H_Q_PITOT_PA)) if pd.notna(means.get(H_Q_PITOT_PA)) else float(means.get(H_Q_AUX_PA))
        row = {
            "source_file": key,
            "alpha_deg": float(means.get(H_ALPHA_DEG, np.nan)),
            "q_inf_Pa": float(q_inf) if pd.notna(q_inf) else np.nan,
            "airspeed_mps": float(means.get(H_V_MS, np.nan)),
            "rho_kgm3": float(means.get(H_RHO_KGM3, np.nan)),
            "sting_normal_N": float(means.get(H_STING_NM, np.nan)),
            "sting_axial_N": float(means.get(H_STING_AX, np.nan)),
            "sting_pitching_Nm": float(means.get(H_STING_PM, np.nan)),
        }
        for col in SCAN_COLS:
            row[col] = float(means.get(col, np.nan))
        rows.append(row)
    out = pd.DataFrame(rows).sort_values("alpha_deg").reset_index(drop=True)
    return out


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    all_dfs = init_data(RAW_DIR)

    means = summarize_means(all_dfs)

    csv_path = PROCESSED_DIR / "means_summary.csv"
    means.to_csv(csv_path, index=False)

    if all_dfs:
        first_key = next(iter(all_dfs))
        print(f"\nFirst file loaded: {first_key} with {len(all_dfs[first_key])} rows")
        print("columns:", all_dfs[first_key].columns.tolist())

if __name__ == "__main__":
    main()
