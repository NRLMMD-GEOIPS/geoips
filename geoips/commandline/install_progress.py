# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Progress display for parallel test-data downloads.

Provides two implementations — rich live display (docker-like) and plain-text
logging — behind a shared duck-typed protocol.  The factory
:func:`create_progress_display` selects the appropriate implementation based
on user preference and TTY detection.
"""

from __future__ import annotations

import sys

from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
)
from rich.console import Console
from rich.live import Live
from rich.text import Text


class PlainProgressDisplay:
    """Line-by-line progress for CI logs and ``--no-rich`` mode."""

    def __init__(self, total: int) -> None:
        self.total = total
        self.completed = 0
        self.failed = 0

    def start(self) -> None:
        """Begin the display (no-op for plain mode)."""
        pass

    def stop(self) -> None:
        """End the display."""
        print(
            f"[GeoIPS] Done: {self.completed} installed, "
            f"{self.failed} failed ({self.total} total)"
        )

    def add_cached(self, name: str) -> None:
        """Log a dataset as already cached and up to date."""
        self.completed += 1
        print(f"[GeoIPS] {name}: \u2713 cached (chunk verified)")

    def log_stale(self, name: str, reason: str) -> None:
        """Log a stale dataset that needs to be re-downloaded."""
        print(f"[GeoIPS] {name}: stale \u2014 {reason}")

    def add_download(self, name: str, total_bytes: int) -> None:
        """Begin tracking a download (byte progress via update_download)."""
        pass  # downloads tracked via update_download

    def update_download(self, name: str, bytes_done: int, total: int) -> None:
        """Update download progress for a dataset being fetched."""
        pct = bytes_done * 100 // total if total else 0
        if pct % 10 == 0 or bytes_done == total:
            print(
                f"[GeoIPS] {name}: Downloading... "
                f"{pct}% ({_fmt_bytes(bytes_done)}/{_fmt_bytes(total)})"
            )

    def mark_download_done(self, name: str) -> None:
        """Mark a download as finished (no-op in plain mode)."""
        pass

    def add_extract(self, name: str, total_files: int) -> None:
        """Begin tracking an archive extraction."""
        print(f"[GeoIPS] {name}: Extracting... 0/{total_files} files")

    def update_extract(self, name: str, files_done: int, total: int) -> None:
        """Update extraction progress for a dataset archive."""
        if files_done % 50 == 0 or files_done == total:
            print(f"[GeoIPS] {name}: Extracting... {files_done}/{total} files")

    def mark_complete(self, name: str) -> None:
        """Mark a dataset as fully downloaded and extracted."""
        self.completed += 1
        print(f"[GeoIPS] {name}: \u2713 installed")

    def mark_failed(self, name: str, reason: str) -> None:
        """Mark a dataset as failed."""
        self.failed += 1
        print(f"[GeoIPS] {name}: \u2717 {reason}")


class RichProgressDisplay:
    """Docker-like live progress display powered by Rich.

    Shows a header with totals, active download/extraction bars with
    spinners, and a scrollable log of completed / failed entries.
    """

    def __init__(self, total: int, is_tty: bool) -> None:
        self.total = total
        self.is_tty = is_tty
        self.completed = 0
        self.failed = 0
        self.downloading = 0
        self.extracting = 0
        self._tasks: dict[str, int] = {}

        self.console = Console()
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.fields[name]:<22s}[/]"),
            TextColumn("{task.fields[phase]:<10s}"),
            BarColumn(bar_width=24),
            TaskProgressColumn(),
            TextColumn("{task.fields[stats]}"),
            TimeRemainingColumn(),
            console=self.console,
            expand=False,
        )
        self.live = Live(
            self.progress,
            console=self.console,
            refresh_per_second=4,
            transient=False,
        )
        self._header_task = None

    def start(self) -> None:
        """Start the live progress display."""
        self.live.start()
        self._header_task = self.progress.add_task(
            self._header_text(),
            total=None,
            name="",
            phase="",
            stats="",
        )

    def stop(self) -> None:
        """Stop the live display and print final summary."""
        self.live.stop()
        self.console.print(
            f"[GeoIPS] Done: {self.completed} installed, "
            f"{self.failed} failed ({self.total} total)"
        )

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def _header_text(self) -> str:
        d, e, c, f, t = (
            self.downloading,
            self.extracting,
            self.completed,
            self.failed,
            self.total,
        )
        return (
            f"[bold]GeoIPS Test Data[/] \u2014 "
            f"{d} downloading \u00b7 "
            f"{e} extracting \u00b7 "
            f"{c} done \u00b7 "
            f"{f} failed "
            f"({t} total)"
        )

    def _refresh_header(self) -> None:
        if self._header_task is not None:
            self.progress.update(
                self._header_task,
                description=self._header_text(),
            )

    def _remove_task(self, name: str) -> None:
        tid = self._tasks.pop(name, None)
        if tid is not None:
            self.progress.remove_task(tid)

    # ------------------------------------------------------------------
    # protocol
    # ------------------------------------------------------------------

    def add_cached(self, name: str) -> None:
        """Log a dataset as already cached and up to date."""
        self.completed += 1
        self._refresh_header()
        self.progress.console.log(
            Text.assemble(
                ("\u2713 ", "green"), (f"{name}  cached (chunk verified)", "")
            )
        )

    def log_stale(self, name: str, reason: str) -> None:
        """Log a stale dataset that needs to be re-downloaded."""
        self.progress.console.log(
            Text.assemble(
                ("\u27f3 ", "yellow"),
                (f"{name}  stale \u2014 {reason}", ""),
            )
        )

    def add_download(self, name: str, total_bytes: int) -> None:
        """Begin tracking a download with a progress bar."""
        self.downloading += 1
        self._refresh_header()
        tid = self.progress.add_task(
            f"[blue]{name}[/]",
            total=total_bytes or 1,
            name=name,
            phase="Download",
            stats=f"0 / {_fmt_bytes(total_bytes)}",
        )
        self._tasks[name] = tid
        self.progress.start_task(tid)

    def update_download(self, name: str, bytes_done: int, total: int) -> None:
        """Update the download progress bar for a dataset."""
        tid = self._tasks.get(name)
        if tid is not None:
            self.progress.update(
                tid,
                completed=bytes_done,
                stats=f"{_fmt_bytes(bytes_done)} / {_fmt_bytes(total)}",
            )

    def mark_download_done(self, name: str) -> None:
        """Mark a download as finished; remove the progress bar."""
        self.downloading -= 1
        self._refresh_header()
        self._remove_task(name)

    def add_extract(self, name: str, total_files: int) -> None:
        """Begin tracking an extraction with a progress bar."""
        self.extracting += 1
        self._refresh_header()
        tid = self.progress.add_task(
            f"[green]{name}[/]",
            total=total_files or 1,
            name=name,
            phase="Extract",
            stats=f"0 / {total_files} files",
        )
        self._tasks[name] = tid
        self.progress.start_task(tid)

    def update_extract(self, name: str, files_done: int, total: int) -> None:
        """Update the extraction progress bar for a dataset."""
        tid = self._tasks.get(name)
        if tid is not None:
            self.progress.update(
                tid,
                completed=files_done,
                stats=f"{files_done} / {total} files",
            )

    def mark_complete(self, name: str) -> None:
        """Mark a dataset as fully downloaded and extracted."""
        self.extracting -= 1
        self.completed += 1
        self._refresh_header()
        self._remove_task(name)
        self.progress.console.log(
            Text.assemble(("\u2713 ", "green"), (f"{name}  installed", ""))
        )

    def mark_failed(self, name: str, reason: str) -> None:
        """Mark a dataset as failed; clean up any active progress bars."""
        tid = self._tasks.get(name)
        if tid is not None:
            phase = self.progress.tasks[tid].fields.get("phase", "")
            if phase == "Download":
                self.downloading -= 1
            elif phase == "Extract":
                self.extracting -= 1
            self._remove_task(name)
        self.failed += 1
        self._refresh_header()
        self.progress.console.log(
            Text.assemble(
                ("\u2717 ", "red"),
                (f"{name}  {reason}", ""),
            )
        )


def create_progress_display(
    total: int,
    use_rich: bool = True,
    is_tty: bool | None = None,
):
    """Return a progress display appropriate for the current environment.

    Parameters
    ----------
    total : int
        Total number of datasets being processed.
    use_rich : bool
        User preference (may be overridden by TTY detection).
    is_tty : bool or None
        If None, auto-detected via ``sys.stdout.isatty()``.

    Returns
    -------
    RichProgressDisplay or PlainProgressDisplay
    """
    if is_tty is None:
        is_tty = sys.stdout.isatty()

    if not use_rich or not is_tty:
        return PlainProgressDisplay(total)
    return RichProgressDisplay(total, is_tty)


def _fmt_bytes(n: int) -> str:
    """Human-readable byte count."""
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.1f} GB"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f} MB"
    if n >= 1_000:
        return f"{n / 1_000:.1f} KB"
    return f"{n} B"
