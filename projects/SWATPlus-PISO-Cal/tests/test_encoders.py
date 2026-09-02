import pytest
import torch

from swatplus_piso.models.encoders import build_encoder
from swatplus_piso.models.point_inverse import PointInverseModel


@pytest.mark.parametrize("name", ["cnn", "tcn", "bilstm", "transformer"])
def test_encoder_and_point_inverse_shapes(name: str) -> None:
    torch.manual_seed(42)
    x = torch.randn(4, 3, 128)
    encoder = build_encoder(name, gauges=3, embedding_dim=32)
    embedding = encoder(x)
    assert embedding.shape == (4, 32)
    model = PointInverseModel(encoder=encoder, embedding_dim=32, parameter_dim=14)
    theta = model(x)
    assert theta.shape == (4, 14)
    assert torch.all((theta >= 0.0) & (theta <= 1.0))
