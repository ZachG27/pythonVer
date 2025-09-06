from pathlib import Path
import pandas as pd
def read_csvs_from_dir(raw_dir: Path, suffix: str = ".csv") -> list[pd.DataFrame]:

    dfs = []
    for p in sorted(raw_dir.glob(f"*{suffix}")):
        try:
            dfs.append(pd.read_csv(p))
        except Exception as e:
            print(f"Warning: failed to read {p}: {e}")
    return dfs

def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parent=True, exist_ok=True)
    df.to_csv(path, index=False)