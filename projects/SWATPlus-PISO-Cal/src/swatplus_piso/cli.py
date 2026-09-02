from __future__ import annotations

import json
from pathlib import Path

import typer

from swatplus_piso.data import load_dataset, load_south_branch_dataset
from swatplus_piso.study_area import A_BASIN

app = typer.Typer(no_args_is_help=True)


@app.command("validate-data")
def validate_data(root: Path) -> None:
    """Validate a generic simulation dataset, including optional paper-reproduction data."""

    dataset = load_dataset(root)
    typer.echo(
        f"PASS theta={dataset.theta.shape} qsim={dataset.qsim.shape} qobs={dataset.qobs.shape}"
    )


@app.command("validate-a-basin-data")
def validate_a_basin_data(root: Path) -> None:
    """Strict validation for the formal South Branch Potomac development dataset."""

    dataset = load_south_branch_dataset(root)
    typer.echo(
        "PASS STUDY_AREA_LOCK=A_SOUTH_BRANCH_POTOMAC "
        f"theta={dataset.theta.shape} qsim={dataset.qsim.shape} qobs={dataset.qobs.shape}"
    )


@app.command("show-a-basin-spec")
def show_a_basin_spec() -> None:
    typer.echo(json.dumps(A_BASIN.to_dict(), indent=2))


@app.command("status")
def status() -> None:
    typer.echo(
        "SWATPlus-PISO-Cal v0.1.0 | FORMAL_STUDY=A_SOUTH_BRANCH_POTOMAC | "
        "paper watershed=method reference only | next=A0 takeover audit"
    )


if __name__ == "__main__":
    app()
