import asyncio
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator, Callable

import simpleobsws


class OBS_Client:
    def __init__(
        self,
        host: str,
        port: int,
        *,
        set_text: Callable[[str], None],
        set_css_classes: Callable[[str], None],
    ) -> None:
        # state
        self._running = True
        # callbacks
        self._set_text = set_text
        self._set_css_classes = set_css_classes
        # websocket
        self._ws = simpleobsws.WebSocketClient(
            url=f'ws://{host}:{port}',
            password=(Path.home() / '.obs-studio-password').read_text().strip(),
            identification_parameters=simpleobsws.IdentificationParameters(ignoreNonFatalRequestChecks=False),
        )

    @asynccontextmanager
    async def _connection(self) -> AsyncIterator[simpleobsws.WebSocketClient]:
        try:
            await self._ws.connect()
            await self._ws.wait_until_identified()
            yield self._ws
        finally:
            await self._ws.disconnect()
            self._set_css_classes('disconnected')

    def stop(self) -> None:
        self._running = False

    async def _worker(self) -> None:
        # connection
        async with self._connection() as conn:
            # main logic starts

            request = simpleobsws.Request('GetVersion')
            response = await conn.call(request)

            if response.ok():
                self._set_css_classes('connected')
                print(f'Request succeeded! Response data: {response.responseData}')

            n = 0
            while self._running:
                n += 1
                text = f'{int(n // 3600):02d}:{int((n % 3600) // 60):02d}:{n % 60:02d}'

                self._set_text(text)

                # heartbeat
                await asyncio.sleep(1)

    def run(self) -> None:
        def launch_worker() -> None:
            asyncio.run(self._worker())
        thread = threading.Thread(target=launch_worker, daemon=True)
        thread.start()
