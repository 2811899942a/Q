from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from swatplus_piso.inverse.models import build_model


@dataclass(frozen=True)
class TrainResult:
    best_val: float
    last_epoch: int
    checkpoint: Path


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True, warn_only=True)


def checkpoint_paths(trial_dir: Path) -> tuple[Path, Path]:
    return trial_dir / "last.pt", trial_dir / "best.pt"


def train_torch_trial(
    name: str,
    config: dict[str, Any],
    qsim: np.ndarray,
    theta: np.ndarray,
    train_index: np.ndarray,
    val_index: np.ndarray,
    seed: int,
    trial_dir: Path,
    device: str,
    max_epochs: int,
    patience: int,
    progress: Callable[[int, float], None] | None = None,
) -> TrainResult:
    """Train or resume one trial; every epoch atomically replaces last/best checkpoints."""

    set_seed(seed)
    trial_dir.mkdir(parents=True, exist_ok=True)
    model = build_model(name, config).to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=float(config.get("lr", 1e-3)),
        weight_decay=float(config.get("weight_decay", 1e-4)),
    )
    loss_fn = nn.MSELoss()
    last_path, best_path = checkpoint_paths(trial_dir)
    start_epoch, best_val, stale = 0, float("inf"), 0
    if last_path.exists():
        payload = torch.load(last_path, map_location=device, weights_only=False)
        if payload["name"] == name and payload["seed"] == seed and payload["config"] == config:
            model.load_state_dict(payload["model"])
            optimizer.load_state_dict(payload["optimizer"])
            start_epoch, best_val, stale = (
                int(payload["epoch"]) + 1,
                float(payload["best_val"]),
                int(payload.get("stale", 0)),
            )
    train_loader = DataLoader(
        TensorDataset(torch.from_numpy(qsim[train_index]), torch.from_numpy(theta[train_index])),
        batch_size=int(config.get("batch_size", 32)),
        shuffle=True,
        num_workers=0,
    )
    val_x, val_y = (
        torch.from_numpy(qsim[val_index]).to(device),
        torch.from_numpy(theta[val_index]).to(device),
    )
    epoch = start_epoch - 1
    for epoch in range(start_epoch, max_epochs):
        model.train()
        for xb, yb in train_loader:
            optimizer.zero_grad(set_to_none=True)
            loss_fn(model(xb.to(device)), yb.to(device)).backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
        model.eval()
        with torch.no_grad():
            val_loss = float(loss_fn(model(val_x), val_y).item())
        payload = {
            "name": name,
            "config": config,
            "seed": seed,
            "model": model.state_dict(),
            "optimizer": optimizer.state_dict(),
            "epoch": epoch,
            "best_val": min(best_val, val_loss),
            "stale": stale,
        }
        torch.save(payload, last_path)
        if val_loss < best_val:
            best_val, stale = val_loss, 0
            payload["best_val"] = best_val
            torch.save(payload, best_path)
        else:
            stale += 1
        if progress:
            progress(epoch, val_loss)
        if stale >= patience:
            break
    if not best_path.exists() or epoch < 0:
        raise RuntimeError("no best checkpoint was written")
    return TrainResult(best_val, epoch, best_path)


def predict_checkpoint(path: Path, qsim: np.ndarray, device: str) -> np.ndarray:
    payload = torch.load(path, map_location=device, weights_only=False)
    model = build_model(str(payload["name"]), dict(payload["config"])).to(device)
    model.load_state_dict(payload["model"])
    model.eval()
    with torch.no_grad():
        return model(torch.from_numpy(np.asarray(qsim, dtype=np.float32)).to(device)).cpu().numpy()
