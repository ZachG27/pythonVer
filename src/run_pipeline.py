from pathlib import Path
import numpy as np
import pandas as pd
from .config import RAWT_DIR, PROCESSED_DIR, FIGS_DIR, C_CHORD_M
from .io_utils import read_csvs_from_dir, write_csv

# def process_directory(rawt_dir: Path, out_dir: Path):
#   out_dir.mkdir(parents=True, exist_ok=True)
#    dfs = read_csvs_from_dir(rawt_dir)
#   cl_rows = []

def main():
    PROCESSED_DIR.mkdir(parents=True,exist_ok=True)
    
    
# Expected CSV headers (exact strings)
H_TEMP_K      = "Atmospheric Temperature [K]"
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

# Geometry file (must be in data/raw/)
GEOM_FILENAME = "port_locations.xlsx"  # columns: port,x_m,y_m,side ('upper'/'lower')


