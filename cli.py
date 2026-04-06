"""CLI interface for the Enterprise Multi-Agent Orchestrator."""


import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

console = Console()


def _print_routing_info(state: dict):
    meta = state.get("routing_metadata", {})
    if not meta:
        return

    method = meta.get("method", "unknown")
    agent = meta.get("selected_agent", "unknown")
    scores = meta.get("keyword_scores", {})

    table = Table(title="Routing Decision", show_header=True)
    table.add_column("Agent", style="cyan")
    table.add_column("Keyword Score", justify="right")
    table.add_column("Selected", justify="center")

    for a in ("finance", "operations", "planning"):
        selected = "✓" if a == agent else ""
        table.add_row(a.title(), str(scores.get(a, 0)), selected)

    console.print(table)
    console.print(f"  Method: [bold]{method}[/bold]\n")


@click.group()
@click.option("--provider", default=None, help="LLM provider (openai, anthropic, ollama)")
@click.pass_context
def main(ctx, provider):
    """Enterprise Multi-Agent Orchestrator CLI."""
    ctx.ensure_object(dict)
    if provider:
        import os
        os.environ["LLM_PROVIDER"] = provider
        from src.config import reset_config
        reset_config()


@main.command()
@click.argument("text")
@click.option("--debug", is_flag=True, help="Show routing decision details")
@click.pass_context
def query(ctx, text, debug):
    """Run a single query through the orchestrator."""
    from src.orchestrator import run_query

    with console.status("[bold green]Processing query..."):
        result = run_query(text)

    if debug:
        _print_routing_info(result)

    final = result.get("final_response", "")
    if final:
        console.print(Panel(Markdown(final), title="Response", border_style="green"))
    else:
        console.print("[yellow]No response generated. Check your query.[/yellow]")


@main.command()
@click.pass_context
def chat(ctx):
    """Interactive chat mode — type queries, get routed responses."""
    from src.orchestrator import run_query

    console.print(
        Panel(
            "[bold]Enterprise Agent Orchestrator[/bold]\n"
            "Type your query and press Enter. Type 'quit' or 'exit' to leave.\n"
            "Prefix with 'debug:' to see routing details.",
            border_style="blue",
        )
    )

    while True:
        try:
            user_input = console.input("\n[bold cyan]You>[/bold cyan] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye.[/dim]")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            console.print("[dim]Goodbye.[/dim]")
            break

        debug = False
        if user_input.lower().startswith("debug:"):
            debug = True
            user_input = user_input[6:].strip()

        with console.status("[bold green]Thinking..."):
            result = run_query(user_input)

        if debug:
            _print_routing_info(result)

        final = result.get("final_response", "")
        if final:
            console.print(Panel(Markdown(final), title="Response", border_style="green"))
        else:
            console.print("[yellow]No response generated.[/yellow]")


if __name__ == "__main__":
    main()
