import asyncio
import base64
from contextlib import asynccontextmanager
from typing import AsyncIterator, Callable

from simpleobsws import Request, WebSocketClient


class VideoPreviewer:
    def __init__(
        self,
        preview: bool,
        preview_width: int,
        preview_height: int,
        preview_interval: float,
        *,
        set_preview_image: Callable[[bytes | None], None],
    ) -> None:
        # attrs
        self._preview = preview
        self._preview_width = preview_width
        self._preview_height = preview_height
        self._preview_interval = preview_interval
        # callbacks
        self._set_preview_image = set_preview_image

    async def _fetch_source_screenshot(self, conn: WebSocketClient) -> bytes:
        # fetch current scene name
        res = await conn.call(Request('GetSceneList'))
        scene_name = res.responseData['currentProgramSceneName']
        # fetch source screenshot
        res = await conn.call(Request('GetSourceScreenshot', {
            'sourceName': scene_name,
            'imageFormat': 'jpg',
            'imageWidth': self._preview_width,
            'imageHeight': self._preview_height,
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
                self._set_preview_image(image_bytes)
                # heartbeat
                await asyncio.sleep(self._preview_interval)
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(e)
                break

    @asynccontextmanager
    async def run(self, conn: WebSocketClient) -> AsyncIterator[None]:
        try:
            if self._preview:
                # start the worker loop
                self._task = asyncio.create_task(self._worker(conn))
            yield
        finally:
            if self._preview and self._task:
                # cancel any task
                self._task.cancel()
                # reset image
                self._set_preview_image(None)
