import asyncio
import base64
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator, Callable

from simpleobsws import Request, WebSocketClient

from obs_dash.run.args import Args

logger = logging.getLogger(__file__)


class VideoPreviewer:
    def __init__(
        self,
        args: Args,
        *,
        set_video_picture_image: Callable[[bytes | None], None],
    ) -> None:
        # attrs
        self._show_video = args.show_video
        self._video_width = args.video_width
        self._video_height = args.video_height
        self._video_sampling_interval = args.video_sampling_interval
        # callbacks
        self._set_video_picture_image = set_video_picture_image

    async def _fetch_source_screenshot(self, conn: WebSocketClient) -> bytes:
        # fetch current scene name
        res = await conn.call(Request('GetSceneList'))
        scene_name = res.responseData['currentProgramSceneName']
        # fetch source screenshot
        res = await conn.call(Request('GetSourceScreenshot', {
            'sourceName': scene_name,
            'imageFormat': 'jpg',
            'imageWidth': self._video_width,
            'imageHeight': self._video_height,
        }))
        # parse result into image bytes
        d = res.responseData
        image_data = d['imageData'].split(',')[1].strip()
        image_bytes = base64.b64decode(image_data)
        # return image bytes
        return image_bytes

    async def _worker(self, conn: WebSocketClient) -> None:
        while True:
            try:
                # fetch source screenshot
                image_bytes = await self._fetch_source_screenshot(conn)
                # set image bytes
                self._set_video_picture_image(image_bytes)
                # heartbeat
                await asyncio.sleep(self._video_sampling_interval)
                continue
            except asyncio.CancelledError as e:
                logger.warning(e)
            except Exception as e:
                logger.info(e)
                break

    @asynccontextmanager
    async def run(self, conn: WebSocketClient) -> AsyncIterator[None]:
        try:
            if self._show_video:
                # start the worker loop
                self._task = asyncio.create_task(self._worker(conn))
            yield
        finally:
            if self._show_video and self._task:
                # cancel any task
                self._task.cancel()
                # reset image
                self._set_video_picture_image(None)
