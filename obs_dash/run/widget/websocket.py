import asyncio
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator, Callable

import simpleobsws
from simpleobsws import Request, WebSocketClient
from websockets.http11 import d


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

    async def _connect(self) -> None:
        await self._ws.connect()
        await self._ws.wait_until_identified()
        self._set_css_classes('connected')

    async def _disconnect(self) -> None:
        await self._ws.disconnect()
        self._set_css_classes('disconnected')

    async def _ping(self, conn: WebSocketClient) -> bool:
        try:
            response = await conn.call(Request('GetVersion'))
            if response.ok():
                self._set_css_classes('connected')
                return True
        except Exception:
            self._set_css_classes('disconnect')
            return False

    def stop(self) -> None:
        self._running = False

    @asynccontextmanager
    async def _connection(self) -> AsyncIterator[simpleobsws.WebSocketClient]:
        try:
            await self._connect()
            yield self._ws
        finally:
            await self._disconnect()

    async def _worker(self) -> None:
        # auto reconnect loop
        while self._running:
            # connection
            async with self._connection() as conn:
                # main logic starts
                n = 0
                while self._running:
                    if not await self._ping(conn):
                        break

                    n += 1
                    text = f'{int(n // 3600):02d}:{int((n % 3600) // 60):02d}:{n % 60:02d}'

                    self._set_text(text)

                    # heartbeat
                    await asyncio.sleep(1)

            # delay before re-connect
            await asyncio.sleep(1)

    def run(self) -> None:
        def launch_worker() -> None:
            asyncio.run(self._worker())
        thread = threading.Thread(target=launch_worker, daemon=True)
        thread.start()
