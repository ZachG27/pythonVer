from __future__ import annotations
from pathlib import Path
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from .config import RAW_DIR, PROCESSED_DIR, FIGS_DIR, C_CHORD_M
# reuse your exact names from the file you showed
from .run_pipeline import H_ALPHA_DEG, H_V_MS, SCAN_COLS

MEANS_FILE = PROCESSED_DIR / "means_summary.csv"  # written by your run_pipeline main()
GEOM_FILE  = RAW_DIR / "port_geometry.csv"        # save your table here with headers: Port,Xm,Y m

def load_means() -> pd.DataFrame:
    df = pd.read_csv(MEANS_FILE)
    # we need these to compute V_local
    need = {"alpha_deg", "airspeed_mps", "q_inf_Pa"}
    missing = need - set(df.columns)
    if missing:
        raise ValueError(f"means_summary.csv is missing columns: {missing}")
    # drop any rows missing essentials
    df = df.dropna(subset=["alpha_deg", "airspeed_mps", "q_inf_Pa"])
    return df

def load_geometry() -> pd.DataFrame:
    """
    Reads geometry file with columns:
      Port, Xm, Y m, side
    Where 'side' is either 'upper' or 'lower'.
    """
    g = pd.read_csv(GEOM_FILE)

    # normalize column names
    cols = {c.lower().strip(): c for c in g.columns}
    def pick(*cands):
        for c in cands:
            if c in cols:
                return cols[c]
        raise KeyError(f"Missing required column among {cands}")

    g = g.rename(columns={
        pick("port"): "port",
        pick("xm", "x m", "x_m"): "x_m",
        pick("y m", "ym", "y_m"): "y_m",
        pick("side"): "side",
    })

    g["port"] = g["port"].astype(int)
    g["side"] = g["side"].str.strip().str.lower()   # normalize case
    g["x_c"] = g["x_m"] / C_CHORD_M

    return g[["port", "x_m", "y_m", "x_c", "side"]].sort_values("port")

def melt_ports(means_row: pd.Series) -> pd.DataFrame:
    """
    Turn one means row into long form with per-port Cp and V_local.
    Uses:
      q_inf_Pa (from means_summary), airspeed_mps (from means_summary),
      scanivalve means (Scanivalve Pressure i [Pa])
    """
    V_inf = float(means_row["airspeed_mps"])
    q_inf = float(means_row["q_inf_Pa"])

    # Build long table of (port -> dP)
    d = {"alpha_deg": float(means_row["alpha_deg"]),
         "airspeed_mps": V_inf,
         "q_inf_Pa": q_inf}
    for col in SCAN_COLS:
        d[col] = float(means_row.get(col, np.nan))
    wide = pd.DataFrame([d])

    long = wide.melt(
        id_vars=["alpha_deg", "airspeed_mps", "q_inf_Pa"],
        value_vars=SCAN_COLS,
        var_name="tap",
        value_name="dP_Pa",
    )
    # extract port number from "Scanivalve Pressure i [Pa]"
    long["port"] = long["tap"].str.extract(r"(\d+)").astype(int)

    # Cp and local velocity
    long["Cp"] = long["dP_Pa"] / long["q_inf_Pa"]
    one_minus = 1.0 - long["Cp"]
    long["V_local"] = long["airspeed_mps"] * np.sqrt(np.clip(one_minus, 0.0, None))
    return long[["alpha_deg", "port", "Cp", "V_local"]]

def pick_runs(df_means: pd.DataFrame, alpha_target=6.0):
    """
    Return indices corresponding to:
      - zero lift (closest |sting_normal_N| to 0 if present, else alpha≈0)
      - ~6 degrees (nearest alpha to +6)
      - stall (max sting_normal_N if present, else max alpha)
    """
    # your means_summary wrote "sting_normal_N" (per your code)
    lift_col = "sting_normal_N" if "sting_normal_N" in df_means.columns else None

    # zero-lift
    if lift_col:
        idx_zero = df_means[lift_col].abs().idxmin()
    else:
        idx_zero = (df_means["alpha_deg"].abs()).idxmin()

    # ~6°
    idx_6 = (df_means["alpha_deg"] - alpha_target).abs().idxmin()

    # stall
    if lift_col:
        idx_stall = df_means[lift_col].idxmax()
    else:
        idx_stall = df_means["alpha_deg"].idxmax()

    return idx_zero, idx_6, idx_stall

def plot_velocity_vs_xc(long_df: pd.DataFrame, geom: pd.DataFrame, title: str, outpath: Path):
    """Plot V_local vs x/c for upper & lower on one figure."""
    d = long_df.merge(geom[["port", "x_c", "side"]], on="port", how="left")

    upper = d[d["side"] == "upper"].sort_values("x_c")
    lower = d[d["side"] == "lower"].sort_values("x_c")

    fig, ax = plt.subplots()
    ax.plot(upper["x_c"], upper["V_local"], marker="o", label="Upper")
    ax.plot(lower["x_c"], lower["V_local"], marker="o", label="Lower")
    ax.set_xlabel("x/c")
    ax.set_ylabel("V_local (m/s)")
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    outpath.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(outpath, dpi=200)
    plt.close(fig)

def main():
    means = load_means()
    geom  = load_geometry()

    idx_zero, idx_6, idx_stall = pick_runs(means, alpha_target=6.0)

    selections = [
        ("zero_lift", means.loc[idx_zero]),
        ("alpha6",    means.loc[idx_6]),
        ("stall",     means.loc[idx_stall]),
    ]

    for label, row in selections:
        long = melt_ports(row)
        title = f"{label.replace('_', ' ').title()} — α = {row['alpha_deg']:.2f}°"
        out = FIGS_DIR / f"V_vs_xc_{label}.png"
        plot_velocity_vs_xc(long, geom, title, out)
        print(f"✅ wrote {out}")

if __name__ == "__main__":
    main()

