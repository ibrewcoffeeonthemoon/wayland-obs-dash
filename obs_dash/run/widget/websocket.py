import asyncio
from typing import Callable


class OBSClient:
    def __init__(
        self,
        update_label: Callable[[str], None]
    ) -> None:
        self.update_label = update_label
        self.running = True

    def stop(self) -> None:
        self.running = False

    async def _worker(self) -> None:
        n = 0
        while self.running:
            n += 1
            text = f'{int(n // 3600):02d}:{int((n % 3600) // 60):02d}:{n % 60:02d}'

            self.update_label(text)

            # heartbeat
            await asyncio.sleep(1)

    def run(self) -> None:
        asyncio.run(self._worker())
