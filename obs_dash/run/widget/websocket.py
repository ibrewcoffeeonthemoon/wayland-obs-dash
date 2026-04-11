import asyncio
from pathlib import Path
from typing import Callable

import simpleobsws


class OBSClient:
    def __init__(
        self,
        host: str = 'localhost',
        port: int = 4455,
        *,
        update_label: Callable[[str], None],
    ) -> None:
        self.update_label = update_label
        self.running = True
        # websocket
        self._ws = simpleobsws.WebSocketClient(
            url=f'ws://{host}:{port}',
            password=(Path.home() / '.obs-studio-password').read_text().strip(),
            identification_parameters=simpleobsws.IdentificationParameters(ignoreNonFatalRequestChecks=False),
        )

    async def connect(self) -> None:
        await self._ws.connect()
        await self._ws.wait_until_identified()

    def stop(self) -> None:
        self.running = False

    async def _worker(self) -> None:
        # connect
        await self.connect()

        request = simpleobsws.Request('GetVersion')  # Build a Request object
        response = await self._ws.call(request)  # Perform the request
        if response.ok():
            print(f'Request succeeded! Response data: {response.responseData}')

        n = 0
        while self.running:
            n += 1
            text = f'{int(n // 3600):02d}:{int((n % 3600) // 60):02d}:{n % 60:02d}'

            self.update_label(text)

            # heartbeat
            await asyncio.sleep(1)

        # disconnect
        await self._ws.disconnect()

    def run(self) -> None:
        asyncio.run(self._worker())
