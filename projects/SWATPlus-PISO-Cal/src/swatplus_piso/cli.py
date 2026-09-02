from __future__ import annotations

from pathlib import Path

import typer

from swatplus_piso.data import load_dataset

app = typer.Typer(no_args_is_help=True)


@app.command("validate-data")
def validate_data(root: Path) -> None:
    dataset = load_dataset(root)
    typer.echo(
        f"PASS theta={dataset.theta.shape} qsim={dataset.qsim.shape} qobs={dataset.qobs.shape}"
    )


@app.command("status")
def status() -> None:
    typer.echo("SWATPlus-PISO-Cal scaffold v0.1.0; follow docs/HANDOFF_NEXT_CHAT_ZH.md")


if __name__ == "__main__":
    app()
