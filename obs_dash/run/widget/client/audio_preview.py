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

    async def _on_input_volume_meters(self, data: dict) -> None:
        # select the data matrix
        mul = data['inputs'][0]['inputLevelsMul']
        # calc the average
        avg_level = (mul[0][0] + mul[1][0])/2
        # set the levelbar
        self._set_audio_levelbar_value(avg_level)

    @asynccontextmanager
    async def run(self, conn: WebSocketClient) -> AsyncIterator[None]:
        try:
            if self._show_audio:
                # subscribe to InputVolumeMeters
                conn.register_event_callback(self._on_input_volume_meters, 'InputVolumeMeters')
            yield
        finally:
            if self._show_audio:
                # unsubscribe to InputVolumeMeters
                conn.deregister_event_callback(self._on_input_volume_meters, 'InputVolumeMeters')
                # reset the levelbar
                self._set_audio_levelbar_value(0)
