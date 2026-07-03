"""
cli/statusbar.py
Renders the bottom status bar.
"""
from rich.text import Text
from rich.panel import Panel

def get_status_bar(latency_ms: int = 42) -> Panel:
    status_text = Text()
    status_text.append("[INFO] Using Binance Futures Testnet", style="info")
    status_text.append("    |    ", style="panel.border")
    status_text.append("[STATUS] All Systems Operational", style="success")
    status_text.append("    |    ", style="panel.border")
    status_text.append(f"[LATENCY] {latency_ms}ms", style="warning")
    status_text.append("    |    ", style="panel.border")
    status_text.append("[VERSION] 1.0.0", style="warning")
    
    return Panel(status_text, style="panel.border", padding=(0, 1))
