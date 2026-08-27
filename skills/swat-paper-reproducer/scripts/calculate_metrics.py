#!/usr/bin/env python3
"""Calculate hydrological metrics from paired observed/simulated flow values."""
import argparse
import math
from pathlib import Path
import pandas as pd


def metrics(obs, sim):
    obs = pd.Series(obs, dtype='float64')
    sim = pd.Series(sim, dtype='float64')
    mask = obs.notna() & sim.notna()
    obs, sim = obs[mask], sim[mask]
    if len(obs) < 2:
        raise ValueError('need at least two paired values')
    r = obs.corr(sim)
    r2 = r * r
    nse = 1 - ((sim - obs) ** 2).sum() / ((obs - obs.mean()) ** 2).sum()
    pbias = 100 * (obs - sim).sum() / obs.sum()
    alpha = sim.std(ddof=1) / obs.std(ddof=1)
    beta = sim.mean() / obs.mean()
    kge = 1 - math.sqrt((r - 1) ** 2 + (alpha - 1) ** 2 + (beta - 1) ** 2)
    rmse = math.sqrt(((sim - obs) ** 2).mean())
    mae = (sim - obs).abs().mean()
    return {
        'n': int(len(obs)), 'R2': r2, 'NSE': nse, 'PBIAS': pbias,
        'KGE': kge, 'RMSE': rmse, 'MAE': mae,
        'mean_obs': obs.mean(), 'mean_sim': sim.mean(),
        'std_obs': obs.std(ddof=1), 'std_sim': sim.std(ddof=1),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument('paired_file', help='CSV/XLSX with observed and simulated columns')
    p.add_argument('--obs-col', required=True)
    p.add_argument('--sim-col', required=True)
    p.add_argument('--out', help='optional CSV output path')
    args = p.parse_args()
    path = Path(args.paired_file)
    df = pd.read_excel(path) if path.suffix.lower() in ['.xlsx', '.xls'] else pd.read_csv(path)
    res = metrics(df[args.obs_col], df[args.sim_col])
    out_df = pd.DataFrame([res])
    print(out_df.to_string(index=False))
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        out_df.to_csv(args.out, index=False)


if __name__ == '__main__':
    main()
