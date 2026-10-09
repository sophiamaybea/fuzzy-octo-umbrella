"""Command-line entrypoint, including an explicitly human-controlled review gate."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from .analysis import compare, discover, inspect, make_context_pack, propose_integration
from .catalogue import connect, list_records, review, upsert
from .github import GitHubClient
from .task_router import compile_task
from .domain_router import plan_specialist_tools
from .neuroimaging import (inspect_local_imaging_header, measure_local_binary_roi_mask, plan_neuroimaging_research)
from .domain_discovery import discover_specialist_repositories

def dump(value):
    print(json.dumps(value, indent=2, ensure_ascii=False))

def main():
    parser = argparse.ArgumentParser(description="Search, inspect and assess public GitHub capability repos")
    subs = parser.add_subparsers(dest="cmd", required=True)
    p = subs.add_parser("search", help="Rank public GitHub repositories")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=10)
    p = subs.add_parser("inspect", help="Read a bounded source snapshot without executing code")
    p.add_argument("repo")
    p.add_argument("--files", type=int, default=7)
    p = subs.add_parser("pack", help="Create a source-linked AI context pack")
    p.add_argument("repo")
    p.add_argument("--out", required=True)
    p.add_argument("--files", type=int, default=7)
    p = subs.add_parser("propose", help="Draft a reviewed integration plan; does not install code")
    p.add_argument("repo")
    p.add_argument("--goal", required=True)
    p = subs.add_parser("compare", help="Compare two bounded repository inspections")
    p.add_argument("left")
    p.add_argument("right")
    p.add_argument("--goal", required=True)
    p = subs.add_parser("scan", help="Collect public candidates into the local registry")
    p.add_argument("--queries", default="config/queries.txt")
    p.add_argument("--limit", type=int, default=8)
    p.add_argument("--out")
    p.add_argument("--db")
    p = subs.add_parser("registry", help="List indexed candidates and review decisions")
    p.add_argument("--status", choices=["CANDIDATE", "APPROVED", "REJECTED"])
    p.add_argument("--db")
    p = subs.add_parser("review", help="Manual approval gate, never exposed over MCP")
    p.add_argument("repo")
    p.add_argument("--decision", required=True, choices=["APPROVED", "REJECTED", "CANDIDATE"])
    p.add_argument("--note", required=True)
    p.add_argument("--db")

    p = subs.add_parser("compile", help="Generate an execution brief without running external tools")
    p.add_argument("task")
    p.add_argument("--tool", action="append", default=[], help="Caller-reported tool, not verified")

    p = subs.add_parser("specialist", help="Propose domain-specific tools without installing code")
    p.add_argument("task")
    p.add_argument("--live", action="store_true", help="Check candidate metadata and search GitHub")
    p.add_argument("--limit", type=int, default=5)

    p = subs.add_parser("imaging-plan", help="Design a non-diagnostic imaging research protocol")
    p.add_argument("question")

    p = subs.add_parser("imaging-inspect", help="Inspect one local DICOM/NIfTI header; no upload")
    p.add_argument("path", help="Local image file; never commit source images or metadata")

    p = subs.add_parser("imaging-mask-volume", help="Measure a local, verified 3D binary NIfTI ROI mask")
    p.add_argument("path", help="Existing segmentation mask; no uploads or diagnosis")

    args = parser.parse_args()
    if args.cmd == "imaging-plan":
        dump(plan_neuroimaging_research(args.question))
        return
    if args.cmd == "imaging-mask-volume":
        dump(measure_local_binary_roi_mask(args.path))
        return
    if args.cmd == "imaging-inspect":
        dump(inspect_local_imaging_header(args.path))
        return
    if args.cmd == "specialist":
        dump(discover_specialist_repositories(args.task, args.limit) if args.live
             else plan_specialist_tools(args.task, args.limit))
        return
    if args.cmd == "compile":
        dump(compile_task(args.task, args.tool))
        return
    if args.cmd == "registry":
        with connect(args.db) as db:
            dump(list_records(db, status=args.status))
        return
    if args.cmd == "review":
        with connect(args.db) as db:
            review(db, args.repo, args.decision, args.note)
        dump({"repo": args.repo, "status": args.decision, "note": args.note})
        return

    with GitHubClient() as client:
        if args.cmd == "search":
            dump(discover(client, args.query, args.limit))
        elif args.cmd == "inspect":
            dump(inspect(client, args.repo, args.files))
        elif args.cmd == "pack":
            content = make_context_pack(inspect(client, args.repo, args.files))
            path = Path(args.out)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            dump({"path": str(path), "characters": len(content)})
        elif args.cmd == "propose":
            dump(propose_integration(inspect(client, args.repo), args.goal))
        elif args.cmd == "compare":
            dump(compare(inspect(client, args.left), inspect(client, args.right), args.goal))
        elif args.cmd == "scan":
            queries = [line.strip() for line in Path(args.queries).read_text(encoding="utf-8").splitlines()
                       if line.strip() and not line.lstrip().startswith("#")]
            if len(queries) > 30:
                raise ValueError("Maximum 30 scan queries to bound rate consumption")
            result = {"queries": {}, "errors": {}, "review_required": True}
            with connect(args.db) as db:
                for query in queries:
                    try:
                        rows = discover(client, query, args.limit)
                        for row in rows:
                            upsert(db, row, query)
                        result["queries"][query] = rows
                    except Exception as exc:
                        result["errors"][query] = f"{type(exc).__name__}: {exc}"
            if args.out:
                output = Path(args.out)
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(json.dumps(result, indent=2), encoding="utf-8")
            dump({"queries_scanned": len(result["queries"]), "errors": result["errors"],
                  "output_file": args.out, "review_required": True})

if __name__ == "__main__":
    main()
