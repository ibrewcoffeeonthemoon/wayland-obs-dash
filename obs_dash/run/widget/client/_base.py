import asyncio
import logging
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator, Callable

from simpleobsws import IdentificationParameters, Request, WebSocketClient

from obs_dash.run.args import Args

from .audio_preview import AudioPreviewer
from .video_preview import VideoPreviewer

logger = logging.getLogger(__file__)


class OBS_Client:
    def __init__(
        self,
        args: Args,
        *,
        set_text: Callable[[str], None],
        set_css_classes: Callable[[str], None],
        set_preview_image: Callable[[bytes | None], None],
        set_audio_levelbar_values: Callable[[float, float], None],
    ) -> None:
        # callbacks
        self._set_text = set_text
        self._set_css_classes = set_css_classes
        # websocket
        self._ws = WebSocketClient(
            url=f'ws://{args.host}:{args.port}',
            password=(Path.home() / '.obs-studio-password').read_text().strip(),
            identification_parameters=IdentificationParameters(
                # eventSubscriptions bitmask: 1023 (All standard events) | 65536 (InputVolumeMeters) = 66559
                eventSubscriptions=66559,
            ),
        )
        # workers
        self._video_previewer = VideoPreviewer(args, set_preview_image=set_preview_image)
        self._audio_previewer = AudioPreviewer(args, set_audio_levelbar_values=set_audio_levelbar_values)

    async def _connect(self) -> None:
        try:
            await self._ws.connect()
            await self._ws.wait_until_identified()
            self._set_css_classes('connected')
            return
        except Exception as e:
            logger.info(e)
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
        except AssertionError as e:
            logger.error(e)
        except Exception as e:
            logger.info(e)
        # set to default state if anything wrong
        self._set_css_classes('disconnect')
        return False

    async def _check_record_status(self, conn: WebSocketClient) -> None:
        try:
            # fetch GetRecordStatus
            res = await conn.call(Request('GetRecordStatus'))
            d = res.responseData
            # assert outputActive
            assert d['outputActive'], 'Not recording. outputActive field is missing'
            # set timecode and state
            timecode = d['outputTimecode'][:-4]
            self._set_text(timecode)
            self._set_css_classes('recording')
            return
        except AssertionError as e:
            logger.info(e)
        except Exception as e:
            logger.info(e)
        # set to default state if anything wrong
        self._set_css_classes('connected')

    @asynccontextmanager
    async def _connection(self) -> AsyncIterator[WebSocketClient]:
        try:
            await self._connect()
            yield self._ws
        finally:
            await self._disconnect()

    async def _worker(self) -> None:
        # auto reconnect loop
        while True:
            async with (
                # connection
                self._connection() as conn,
                # tasks
                self._video_previewer.run(conn),
                self._audio_previewer.run(conn),
            ):
                # start main logic loop
                while True:
                    # check connection
                    if not await self._ping(conn):
                        # when ping failed, the loop breaks, all task is cancelled
                        break
                    # check record status
                    await self._check_record_status(conn)
                    # heartbeat
                    await asyncio.sleep(1)

            # delay before re-connect
            await asyncio.sleep(1)

    def run(self) -> None:
        # asyncio worker
        def launch_worker() -> None:
            asyncio.run(self._worker())
        # start asyncio worker in a separated thread
        thread = threading.Thread(target=launch_worker, daemon=True)
        thread.start()
