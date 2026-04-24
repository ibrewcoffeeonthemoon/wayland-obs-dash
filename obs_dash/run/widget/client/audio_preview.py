from contextlib import asynccontextmanager
from typing import AsyncIterator, Callable

from simpleobsws import WebSocketClient

from obs_dash.run.args import Args


class AudioPreviewer:
    def __init__(
        self,
        args: Args,
        *,
        set_audio_levelbar_value: Callable[[float | None], None],
    ) -> None:
        # attrs
        self._show_audio = args.show_audio
        # callbacks
        self._set_audio_levelbar_value = set_audio_levelbar_value

    @asynccontextmanager
    async def run(self, conn: WebSocketClient) -> AsyncIterator[None]:
        try:
            if self._show_audio:
                self._set_audio_levelbar_value(0.6)  # TODO: dummy value
            yield
        finally:
            if self._show_audio:
                # reset the
                self._set_audio_levelbar_value(0)
