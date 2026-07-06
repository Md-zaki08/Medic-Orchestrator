import asyncio
import json
import sys
import os
import uuid
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.state import InputManifest, MedWasteSessionState
from src.graph import MedWasteGraphOrchestrator

console = Console()


def load_fixture(path: str) -> InputManifest:
    with open(path, "r") as f:
        data = json.load(f)
    return InputManifest(**data)


async def run_scenario(manifest: InputManifest, label: str = "scenario"):
    session = MedWasteSessionState(
        session_id=f"{label}-{uuid.uuid4().hex[:8]}",
        input_manifest=manifest,
    )

    orchestrator = MedWasteGraphOrchestrator()
    result = await orchestrator.execute_run(session)

    console.print(Panel(f"[bold cyan]{label.upper()}[/bold cyan]", expand=False))

    table = Table(title="Pipeline Status")
    table.add_column("Step", style="cyan")
    table.add_column("Result", style="green")

    for step in result.execution_history:
        if "ERROR" in step or "FAULT" in step or "VETO" in step:
            table.add_row("⚠", f"[red]{step}[/red]")
        elif "APPROVED" in step:
            table.add_row("✓", f"[green]{step}[/green]")
        else:
            table.add_row("→", step)

    console.print(table)

    if result.classification:
        console.print(f"[bold]Classified as:[/bold] {result.classification.assigned_class.value} "
                       f"(confidence: {result.classification.confidence:.0%})")
        if result.classification.reconciliation_notes:
            console.print(f"[dim]Notes: {result.classification.reconciliation_notes}[/dim]")

    if result.routing:
        console.print(f"[bold]Routing:[/bold] {result.routing.selected_facility_name} | "
                       f"Cost: ${result.routing.estimated_cost_usd:,.0f} | "
                       f"Risk: {result.routing.route_risk_exposure_index:.2f}")

    if result.compliance:
        status = "✓ COMPLIANT" if result.compliance.is_compliant else "✗ NON-COMPLIANT"
        color = "green" if result.compliance.is_compliant else "red"
        console.print(f"[bold]Compliance:[/bold] [{color}]{status}[/{color}]")
        if result.compliance.violations:
            for v in result.compliance.violations:
                console.print(f"  [red]Violation: {v}[/red]")
        if result.compliance.final_disposal_method:
            console.print(f"[bold]Disposal Method:[/bold] {result.compliance.final_disposal_method.value}")

    if result.execution:
        status_color = {
            "APPROVED": "green",
            "VETOED": "red",
            "PENDING_HUMAN_APPROVAL": "yellow",
        }.get(result.execution.status.value, "white")
        console.print(f"[bold]Execution Status:[/bold] [{status_color}]{result.execution.status.value}[/{status_color}]")
        console.print(f"[dim]Audit Hash: {result.execution.audit_hash[:16]}...[/dim]")

    console.print("─" * 60)
    return result


async def run_all_fixtures():
    fixtures_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fixtures")
    if not os.path.exists(fixtures_dir):
        console.print("[red]No fixtures directory found.[/red]")
        return

    fixture_files = sorted([f for f in os.listdir(fixtures_dir) if f.endswith(".json")])

    if not fixture_files:
        console.print("[yellow]No fixture JSON files found.[/yellow]")
        return

    console.print(Panel("[bold]Running All Golden Fixtures[/bold]", expand=False))

    for fixture_file in fixture_files:
        path = os.path.join(fixtures_dir, fixture_file)
        label = fixture_file.replace(".json", "")
        try:
            manifest = load_fixture(path)
            await run_scenario(manifest, label)
        except Exception as e:
            console.print(f"[red]Error running {fixture_file}: {e}[/red]")

    console.print("[bold green]All fixtures complete.[/bold green]")


def cli_entry():
    if len(sys.argv) > 1 and sys.argv[1] == "--scenario":
        path = sys.argv[2]
        manifest = load_fixture(path)
        asyncio.run(run_scenario(manifest, os.path.basename(path).replace(".json", "")))
    elif len(sys.argv) > 1 and sys.argv[1] == "--all":
        asyncio.run(run_all_fixtures())
    else:
        console.print("[bold]Medic Orchestrator - CLI Runner[/bold]")
        console.print("Usage:")
        console.print("  python src/main.py --scenario <fixture_path>    Run a single fixture")
        console.print("  python src/main.py --all                        Run all fixtures")
        console.print("  streamlit run src/app/ui.py                     Launch Web UI")


if __name__ == "__main__":
    cli_entry()
