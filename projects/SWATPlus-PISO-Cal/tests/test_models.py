import torch

from swatplus_piso.models.encoders import build_encoder


def test_all_encoders_return_fixed_embedding() -> None:
    x = torch.randn(2, 3, 140)
    for name in ("cnn", "tcn", "bilstm", "transformer"):
        model = build_encoder(name, gauges=3, embedding_dim=32)
        y = model(x)
        assert y.shape == (2, 32)
        assert torch.isfinite(y).all()
