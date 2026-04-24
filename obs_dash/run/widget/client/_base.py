import asyncio
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator, Callable

import simpleobsws
from simpleobsws import Request, WebSocketClient

from .video_preview import VideoPreviewer


class OBS_Client:
    def __init__(
        self,
        host: str,
        port: int,
        preview: bool,
        preview_width: int,
        preview_height: int,
        preview_interval: float,
        *,
        set_text: Callable[[str], None],
        set_css_classes: Callable[[str], None],
        set_preview_image: Callable[[bytes | None], None],
    ) -> None:
        # callbacks
        self._set_text = set_text
        self._set_css_classes = set_css_classes
        self._set_preview_image = set_preview_image
        # websocket
        self._ws = simpleobsws.WebSocketClient(
            url=f'ws://{host}:{port}',
            password=(Path.home() / '.obs-studio-password').read_text().strip(),
            identification_parameters=simpleobsws.IdentificationParameters(ignoreNonFatalRequestChecks=False),
        )
        # workers
        self._video_previewer = VideoPreviewer(
            preview,
            preview_width,
            preview_height,
            preview_interval,
            set_preview_image=set_preview_image
        )

    async def _connect(self) -> None:
        try:
            await self._ws.connect()
            await self._ws.wait_until_identified()
            self._set_css_classes('connected')
            return
        except Exception as e:
            print(e)
        # set to default state if anything wrong
        self._set_css_classes('disconnect')

    async def _disconnect(self) -> None:
        await self._ws.disconnect()
        self._set_css_classes('disconnected')

    async def _ping(self, conn: WebSocketClient) -> bool:
        try:
            # fetch GetVersion
            res = await conn.call(Request('GetVersion'))
            # assert valid response
            assert res.ok()
            # return ping success
            return True
        except AssertionError:
            pass
        except Exception as e:
            print(e)
        # set to default state if anything wrong
        self._set_css_classes('disconnect')
        return False

    async def _check_record_status(self, conn: WebSocketClient) -> None:
        try:
            # fetch GetRecordStatus
            res = await conn.call(Request('GetRecordStatus'))
            d = res.responseData
            # assert outputActive
            assert d['outputActive']
            # set timecode and state
            timecode = d['outputTimecode'][:-4]
            self._set_text(timecode)
            self._set_css_classes('recording')
            return
        except AssertionError:
            pass
        except Exception as e:
            print(e)
        # set to default state if anything wrong
        self._set_css_classes('connected')

    @asynccontextmanager
    async def _connection(self) -> AsyncIterator[simpleobsws.WebSocketClient]:
        try:
            await self._connect()
            yield self._ws
        finally:
            await self._disconnect()

    async def _worker(self) -> None:
        # auto reconnect loop
        while True:
            # connection
            async with (
                self._connection() as conn,
                self._video_previewer.run(conn)
            ):
                # start main logic loop
                while True:
                    # check connection
                    if not await self._ping(conn):
                        break
                    # check record status
                    await self._check_record_status(conn)
                    # heartbeat
                    await asyncio.sleep(1)

            # delay before re-connect
            await asyncio.sleep(1)

    def run(self) -> None:
        def launch_worker() -> None:
            asyncio.run(self._worker())
        thread = threading.Thread(target=launch_worker, daemon=True)
        thread.start()
