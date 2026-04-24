import math
from contextlib import asynccontextmanager
from typing import AsyncIterator, Callable

from simpleobsws import WebSocketClient

from obs_dash.run.args import Args


def linear_to_db(linear_val: float) -> float:
    if linear_val <= 0.0000001:  # Avoid log(0)
        return -100.0
    return 20 * math.log10(linear_val)


def db_to_ui_percent(db_val: float, min_db: float = -60.0) -> float:
    if db_val < min_db:
        return 0.0
    if db_val > 0:
        return 1.0
    # Linear mapping of the dB range
    return (db_val - min_db) / (0.0 - min_db)


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
        # process values
        peak_val = sum(ch[0] for ch in mul)/len(mul)
        db = linear_to_db(peak_val)
        ui_value = db_to_ui_percent(db)
        # set the levelbar
        self._set_audio_levelbar_value(ui_value)

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
