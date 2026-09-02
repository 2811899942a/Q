from __future__ import annotations

from typing import Any

import torch
from torch import nn


def train_npe(
    theta_normalized: torch.Tensor,
    q_scaled: torch.Tensor,
    encoder: nn.Module,
    density: str = "maf",
    max_num_epochs: int = 300,
) -> Any:
    """Train a neural posterior estimator with sbi>=0.27.

    This function intentionally accepts only simulator pairs `(theta, qsim)`.
    Observed objective values are handled by the separate sequential optimizer.
    """

    try:
        from sbi.inference import NPE
        from sbi.neural_nets import posterior_nn
        from sbi.utils import BoxUniform
    except ImportError as exc:
        raise RuntimeError('Install the optional dependency with: pip install -e ".[sbi]"') from exc

    if theta_normalized.ndim != 2 or q_scaled.ndim != 3:
        raise ValueError("expected theta [N,P] and q_scaled [N,G,T]")
    prior = BoxUniform(
        low=torch.zeros(theta_normalized.shape[1], device=theta_normalized.device),
        high=torch.ones(theta_normalized.shape[1], device=theta_normalized.device),
    )
    density_builder = posterior_nn(
        model=density,
        embedding_net=encoder,
        z_score_x="none",
        z_score_y="none",
    )
    inference = NPE(prior=prior, density_estimator=density_builder)
    density_estimator = inference.append_simulations(theta_normalized, q_scaled).train(
        max_num_epochs=max_num_epochs
    )
    return inference.build_posterior(density_estimator)
