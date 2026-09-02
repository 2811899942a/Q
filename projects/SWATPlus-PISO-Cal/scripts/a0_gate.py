from __future__ import annotations

import argparse

from a0_utils import load_provenance, make_paths

from swatplus_piso.audit.leakage import run_gate, run_leakage_audit


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate the A0 South Branch takeover gate")
    parser.add_argument("--root", "--asset-root", dest="root")
    parser.add_argument("--config")
    parser.add_argument("--out")
    parser.add_argument("--qobs-root", help="override the external clean observation directory")
    args = parser.parse_args()
    paths = make_paths(args.root, args.config, args.out, args.qobs_root)
    provenance = load_provenance(paths)
    run_leakage_audit(paths, provenance)
    result = run_gate(paths, provenance)
    dataset = result.get("dataset_detail", {})
    actual_shapes = dataset.get("actual_shapes", {})
    runner = result.get("runner_detail", {})
    max_daily = max((float(case.get("max_abs_diff", 0.0)) for case in runner.get("cases", [])), default=float("nan"))
    max_objective = max((float(case.get("objective_abs_diff", 0.0)) for case in runner.get("cases", [])), default=float("nan"))
    print("A0_SOUTH_BRANCH_PISO_TAKEOVER_AUDIT")
    print(f"STUDY_AREA={result['study_area']}")
    print(f"SWAT_REVISION={result['swat_revision']}")
    print(f"PARAM_DIM={result['parameter_dim']}")
    print("GAUGES=3")
    print(f"BROAD_POOL={result['counts']['broad_rows']}")
    print(f"OPTIMIZER_DIRECTED_POOL={result['counts']['optimizer_directed_rows']}")
    print(f"UNKNOWN_POOL={result['counts']['unknown_rows']}")
    print(f"THETA_SHAPE={actual_shapes.get('theta')}")
    print(f"QSIM_SHAPE={actual_shapes.get('qsim')}")
    print(f"QOBS_SHAPE={actual_shapes.get('qobs')}")
    print("PAPER_WATERSHED_CONTAMINATION=NO" if not result["paper_watershed_contamination"] else "PAPER_WATERSHED_CONTAMINATION=YES")
    print("VALIDATION_LEAKAGE=NO" if result["checks"]["validation_final_leakage"] else "VALIDATION_LEAKAGE=YES")
    print("FINAL_TEST_LEAKAGE=NO" if result["checks"]["validation_final_leakage"] else "FINAL_TEST_LEAKAGE=YES")
    print(f"OLD_NEW_RUNNER_EQUIVALENCE={'PASS' if result['runner_equivalence_pass'] else 'FAIL'}")
    print(f"OBJECTIVE_EQUIVALENCE={'PASS' if result['objective_equivalence_pass'] else 'FAIL'}")
    print(f"MAX_DAILY_ABS_DIFF={max_daily:.17g}")
    print(f"MAX_OBJECTIVE_ABS_DIFF={max_objective:.17g}")
    print(f"A0_GATE={result['gate']}")
    print(f"BLOCKING_ISSUES={result['blocking_issues'] or 'NONE'}")
    return 0 if result["gate"] == "A0_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
