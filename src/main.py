"""
00-flagship/regulatory-precheck-agent/main.py
=====================================

Regulatory Documentation Pre-Check Agent
---------------------------------------
Cohere-powered assistant that scans medical-device submission packages
(Saudi FDA, UAE MoHAP, IMDRF, KFDA formats) for:
  - Missing documents
  - Format-compliance issues
  - Regulatory language gaps
BEFORE submission — saving weeks of back-and-forth with regulators.

Architecture:
  1. Index regulatory requirement documents into a vector store (Cohere Embed v3)
  2. Parse the submission package (JSON manifest of submitted documents)
  3. For each requirement clause, retrieve relevant context (Cohere Rerank)
  4. Use Cohere Command R+ with tool use to:
     - Validate submission completeness
     - Flag missing documents
     - Suggest language improvements
     - Cite the specific regulatory clause that triggered the finding
  5. Output a structured findings report (JSON + human-readable markdown)

Usage:
    python main.py --submission sample_submission/sample_package.json
    python main.py --submission sample_submission/sample_package.json --format json
    python main.py --submission sample_submission/sample_package.json --verbose
"""

from __future__ import annotations

import json
import os
import sys
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import click
import cohere
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

load_dotenv()

ROOT = Path(__file__).parent
CORPUS_DIR = ROOT / "regulatory_corpus"
SUBMISSIONS_DIR = ROOT / "sample_submission"

console = Console()

COHERE_MODEL = "command-r-plus"  # frontier model
COHERE_EMBED_MODEL = "embed-english-v3.0"
COHERE_RERANK_MODEL = "rerank-english-v3.0"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class RequirementClause:
    """A specific clause from a regulatory document."""

    source_file: str
    clause_id: str  # e.g. "SFDA-MD-5.1"
    jurisdiction: str  # "Saudi FDA", "UAE MoHAP", "IMDRF", "KFDA"
    text: str
    input_type: str  # "embedding" for v3 (semantic search)

    def __post_init__(self) -> None:
        self.input_type = "embedding"  # required by Cohere Embed v3


@dataclass
class SubmissionPackage:
    """A medical-device regulatory submission package."""

    device_name: str
    jurisdiction: str
    submitted_documents: list[dict[str, str]]  # {"name":..., "type":..., "path":...}
    applicant: str = ""
    submission_date: str = ""

    @classmethod
    def from_json(cls, path: Path) -> "SubmissionPackage":
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            device_name=data["device_name"],
            jurisdiction=data["jurisdiction"],
            submitted_documents=data["submitted_documents"],
            applicant=data.get("applicant", ""),
            submission_date=data.get("submission_date", ""),
        )


@dataclass
class Finding:
    """A pre-check finding."""

    severity: str  # "critical" | "warning" | "info"
    category: str  # "missing_document" | "format_issue" | "language_gap"
    title: str
    description: str
    cited_clause: str  # e.g. "SFDA-MD-5.1 (Saudi FDA Medical Devices 5.1)"
    suggested_fix: str = ""


# ---------------------------------------------------------------------------
# Cohere wrapper
# ---------------------------------------------------------------------------


class CohereClient:
    """Thin wrapper around the Cohere SDK for this project."""

    def __init__(self, api_key: str | None = None) -> None:
        api_key = api_key or os.getenv("COHERE_API_KEY")
        if not api_key:
            console.print(
                "[red]✗ COHERE_API_KEY not set. Copy .env.example to .env and add your key.[/red]"
            )
            sys.exit(1)
        self.client = cohere.Client(api_key=api_key)
        self._corpus_embeddings: list[list[float]] = []
        self._clauses: list[RequirementClause] = []

    # -- Embedding ---------------------------------------------------------

    def index_corpus(self, corpus_dir: Path) -> None:
        """Read .txt files from corpus_dir, split into clauses, embed."""
        clauses: list[RequirementClause] = []
        for txt_file in sorted(corpus_dir.glob("*.txt")):
            content = txt_file.read_text(encoding="utf-8")
            for clause_block in content.split("\n\n---\n\n"):
                clause_block = clause_block.strip()
                if not clause_block:
                    continue
                # First line of each block is the clause_id (e.g. "[SFDA-MD-5.1]")
                lines = clause_block.split("\n", 2)
                if len(lines) < 2:
                    continue
                clause_id = lines[0].strip("[]")
                jurisdiction_line = lines[1].strip()
                body = lines[2].strip() if len(lines) > 2 else ""
                clauses.append(
                    RequirementClause(
                        source_file=txt_file.name,
                        clause_id=clause_id,
                        jurisdiction=jurisdiction_line,
                        text=body,
                        input_type="embedding",
                    )
                )

        if not clauses:
            console.print(f"[red]✗ No clauses found in {corpus_dir}[/red]")
            sys.exit(1)

        # Batch embed (Cohere allows up to 96 inputs per call)
        texts = [c.text for c in clauses]
        BATCH = 96
        all_embeddings: list[list[float]] = []
        for i in range(0, len(texts), BATCH):
            batch = texts[i : i + BATCH]
            response = self.client.embed(
                texts=batch,
                model=COHERE_EMBED_MODEL,
                input_type="classification",
            )
            all_embeddings.extend(response.embeddings)

        self._corpus_embeddings = all_embeddings
        self._clauses = clauses
        console.print(
            f"[green]✓ Indexed {len(clauses)} clauses across "
            f"{len({c.source_file for c in clauses})} regulatory documents[/green]"
        )

    # -- Retrieval ---------------------------------------------------------

    def retrieve(self, query: str, top_k: int = 5) -> list[RequirementClause]:
        """Semantic search over the indexed corpus, then rerank."""
        # Step 1: embed the query
        q_emb = self.client.embed(
            texts=[query], model=COHERE_EMBED_MODEL, input_type="search_query"
        ).embeddings[0]

        # Step 2: cosine similarity (small corpus — no need for a vector DB)
        import math

        def cosine(a: list[float], b: list[float]) -> float:
            return sum(x * y for x, y in zip(a, b)) / (
                math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(x * x for x in b))
            )

        scored = [
            (cosine(q_emb, emb), clause)
            for emb, clause in zip(self._corpus_embeddings, self._clauses)
        ]
        scored.sort(key=lambda x: x[0], reverse=True)
        top = [c for _, c in scored[: max(top_k * 3, 15)]]

        # Step 3: rerank with Cohere Rerank
        if len(top) > 1:
            rerank_response = self.client.rerank(
                model=COHERE_RERANK_MODEL,
                query=query,
                documents=[c.text for c in top],
                top_n=top_k,
            )
            reranked = [top[r.index] for r in rerank_response.results]
            return reranked
        return top[:top_k]

    # -- Generation (with tool use) ---------------------------------------

    def validate_submission(
        self, submission: SubmissionPackage, relevant_clauses: list[RequirementClause]
    ) -> list[Finding]:
        """Use Command R+ with tool use to validate the submission."""
        # Tool definition: the LLM can call this to look up a specific clause
        tools = [
            {
                "name": "lookup_clause",
                "description": "Look up a specific regulatory clause by its ID "
                "(e.g. 'SFDA-MD-5.1'). Returns the clause text.",
                "parameter_definitions": {
                    "clause_id": {
                        "description": "The clause identifier",
                        "type": "str",
                        "required": True,
                    }
                },
            }
        ]

        # Build the prompt
        clauses_context = "\n\n".join(
            f"[{c.clause_id}] ({c.jurisdiction})\n{c.text}" for c in relevant_clauses
        )

        submitted_docs = "\n".join(
            f"  - {d['name']} (type: {d['type']})"
            for d in submission.submitted_documents
        )

        prompt = textwrap.dedent(
            f"""
            You are a regulatory pre-check agent for medical-device submissions.

            # Submission under review
            - Device: {submission.device_name}
            - Jurisdiction: {submission.jurisdiction}
            - Applicant: {submission.applicant or '(not provided)'}
            - Date: {submission.submission_date or '(not provided)'}

            # Submitted documents
            {submitted_docs}

            # Relevant regulatory clauses
            {clauses_context}

            # Your task
            For each clause above, determine whether the submitted documents satisfy it.
            Flag:
              1. **Missing documents** — a required document is not in the submission
              2. **Format issues** — a document is present but doesn't match the required format
              3. **Language gaps** — required wording, declarations, or technical specs missing

            For each finding, output EXACTLY this JSON structure (a single JSON array):

            [
              {{
                "severity": "critical|warning|info",
                "category": "missing_document|format_issue|language_gap",
                "title": "Short title (5-8 words)",
                "description": "1-2 sentence description of the issue",
                "cited_clause": "The clause_id that triggered this finding (e.g. 'SFDA-MD-5.1')",
                "suggested_fix": "Concrete actionable fix"
              }}
            ]

            If the submission is fully compliant, return an empty array [].
            Only output the JSON array — no preamble, no explanation.
            """
        ).strip()

        # Use Cohere chat with tool use
        response = self.client.chat(
            message=prompt,
            model=COHERE_MODEL,
            tools=tools,
            preamble=(
                "You are a meticulous regulatory compliance reviewer for medical devices. "
                "You produce structured JSON findings with grounded citations to specific "
                "regulatory clause IDs. You never invent clause IDs — you only cite clauses "
                "from the context provided."
            ),
        )

        return self._parse_findings(response.text, relevant_clauses)

    def _parse_findings(
        self, text: str, clauses: list[RequirementClause]
    ) -> list[Finding]:
        """Parse the LLM's JSON output into Finding objects."""
        # Extract the JSON array (LLM may include surrounding text)
        try:
            start = text.index("[")
            end = text.rindex("]") + 1
            data = json.loads(text[start:end])
        except (ValueError, json.JSONDecodeError) as e:
            console.print(f"[red]✗ Failed to parse LLM output as JSON: {e}[/red]")
            console.print(f"[dim]Raw output:[/dim]\n{text}")
            return []

        valid_clause_ids = {c.clause_id for c in clauses}
        findings: list[Finding] = []
        for item in data:
            cited = item.get("cited_clause", "")
            if cited and cited not in valid_clause_ids:
                # LLM hallucinated a clause ID — flag and skip the citation
                console.print(
                    f"[yellow]⚠ LLM cited unknown clause '{cited}' — "
                    "removing citation[/yellow]"
                )
                item["cited_clause"] = "(unverified)"
            findings.append(
                Finding(
                    severity=item.get("severity", "info"),
                    category=item.get("category", "info"),
                    title=item.get("title", "Untitled finding"),
                    description=item.get("description", ""),
                    cited_clause=item.get("cited_clause", ""),
                    suggested_fix=item.get("suggested_fix", ""),
                )
            )
        return findings


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def render_markdown_report(
    submission: SubmissionPackage, findings: list[Finding]
) -> str:
    """Render findings as a markdown report."""
    lines = [
        f"# Pre-Check Report — {submission.device_name}",
        "",
        f"- **Jurisdiction**: {submission.jurisdiction}",
        f"- **Applicant**: {submission.applicant or '(not provided)'}",
        f"- **Date**: {submission.submission_date or '(not provided)'}",
        f"- **Submitted documents**: {len(submission.submitted_documents)}",
        f"- **Findings**: {len(findings)} "
        f"({sum(1 for f in findings if f.severity == 'critical')} critical, "
        f"{sum(1 for f in findings if f.severity == 'warning')} warning, "
        f"{sum(1 for f in findings if f.severity == 'info')} info)",
        "",
    ]

    if not findings:
        lines.append("## ✅ All checks passed")
        lines.append("")
        lines.append(
            "No missing documents, format issues, or language gaps detected "
            "against the indexed regulatory corpus."
        )
        return "\n".join(lines)

    by_severity: dict[str, list[Finding]] = {"critical": [], "warning": [], "info": []}
    for f in findings:
        by_severity.setdefault(f.severity, "info").append(f) if isinstance(
            by_severity.get(f.severity), list
        ) else None
        by_severity[f.severity].append(f)

    for sev in ["critical", "warning", "info"]:
        items = by_severity.get(sev, [])
        if not items:
            continue
        icon = {"critical": "🔴", "warning": "🟡", "info": "🔵"}[sev]
        lines.append(f"## {icon} {sev.upper()} ({len(items)})")
        lines.append("")
        for i, f in enumerate(items, 1):
            lines.append(f"### {i}. {f.title}")
            lines.append("")
            lines.append(f"- **Category**: `{f.category}`")
            lines.append(f"- **Cited clause**: `{f.cited_clause}`")
            lines.append(f"- **Description**: {f.description}")
            if f.suggested_fix:
                lines.append(f"- **Suggested fix**: {f.suggested_fix}")
            lines.append("")

    return "\n".join(lines)


def render_rich_table(findings: list[Finding]) -> None:
    """Render findings as a rich table in the console."""
    if not findings:
        console.print("[green]✅ All checks passed — no findings[/green]")
        return

    table = Table(title="Pre-Check Findings", show_lines=True)
    table.add_column("Severity", style="bold")
    table.add_column("Category")
    table.add_column("Title")
    table.add_column("Cited Clause", style="cyan")
    table.add_column("Suggested Fix")

    sev_color = {"critical": "red", "warning": "yellow", "info": "blue"}
    for f in findings:
        table.add_row(
            f"[{sev_color.get(f.severity, 'white')}]{f.severity.upper()}[/{sev_color.get(f.severity, 'white')}]",
            f.category,
            f.title,
            f.cited_clause,
            f.suggested_fix[:80] + ("..." if len(f.suggested_fix) > 80 else ""),
        )
    console.print(table)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


@click.command()
@click.option(
    "--submission",
    "submission_path",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Path to the submission package JSON file.",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "markdown"]),
    default="table",
    help="Output format for the findings report.",
)
@click.option("--verbose", is_flag=True, help="Show retrieval steps and full LLM output.")
def main(
    submission_path: Path, output_format: str, verbose: bool
) -> None:
    """Run the regulatory pre-check agent on a submission package."""
    console.print(
        Panel.fit(
            "[bold]Regulatory Documentation Pre-Check Agent[/bold]\n"
            "[dim]Cohere Command R+ · Embed v3 · Rerank · Tool Use[/dim]",
            border_style="purple",
        )
    )

    # 1. Load submission
    submission = SubmissionPackage.from_json(submission_path)
    console.print(
        f"[bold]Submission loaded:[/bold] {submission.device_name} "
        f"({submission.jurisdiction}) — {len(submission.submitted_documents)} documents"
    )

    # 2. Initialize Cohere + index corpus
    client = CohereClient()
    client.index_corpus(CORPUS_DIR)

    # 3. Retrieve relevant clauses for this submission
    query = (
        f"Medical device submission requirements for {submission.jurisdiction}: "
        f"required documents, format specifications, language requirements, "
        f"technical file contents, IFU requirements, clinical evaluation requirements."
    )
    if verbose:
        console.print(f"[dim]Retrieval query: {query}[/dim]")

    relevant = client.retrieve(query, top_k=10)
    console.print(
        f"[green]✓ Retrieved {len(relevant)} relevant clauses[/green]"
    )
    if verbose:
        for c in relevant:
            console.print(f"  [dim]- {c.clause_id} ({c.jurisdiction})[/dim]")

    # 4. Validate submission with Command R+
    console.print("[bold]Validating submission with Command R+...[/bold]")
    findings = client.validate_submission(submission, relevant)

    # 5. Output report
    if output_format == "table":
        render_rich_table(findings)
    elif output_format == "json":
        print(
            json.dumps(
                [f.__dict__ for f in findings], indent=2, ensure_ascii=False
            )
        )
    else:  # markdown
        print(render_markdown_report(submission, findings))

    # Summary
    n_crit = sum(1 for f in findings if f.severity == "critical")
    n_warn = sum(1 for f in findings if f.severity == "warning")
    n_info = sum(1 for f in findings if f.severity == "info")

    console.print()
    console.print(
        f"[bold]Summary:[/bold] {len(findings)} findings "
        f"({n_crit} critical, {n_warn} warning, {n_info} info)"
    )
    if n_crit > 0:
        console.print(
            f"[red]✗ Submission has {n_crit} critical issue(s) — fix before submitting.[/red]"
        )
        sys.exit(1)
    else:
        console.print(
            "[green]✓ No critical issues — submission may proceed.[/green]"
        )


if __name__ == "__main__":
    main()
