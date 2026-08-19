from collections.abc import Iterable, Iterator

from rich.console import Console
from rich.progress import track

console = Console()


def progress_track[Item](
    items: Iterable[Item], description: str, total: int | None = None
) -> Iterator[Item]:
    yield from track(items, description=description, total=total)
