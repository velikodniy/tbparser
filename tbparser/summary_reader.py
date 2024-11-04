from __future__ import annotations

from collections.abc import Iterable
from collections.abc import Iterator
from pathlib import Path
from typing import Any
from typing import NamedTuple
from typing import TYPE_CHECKING

import imageio

from tbparser.events_reader import EventReadingError
from tbparser.events_reader import EventsFileReader

if TYPE_CHECKING:
    import numpy as np


class SummaryItem(NamedTuple):
    tag: str
    step: int
    wall_time: Any
    value: Any
    type: str


def _get_scalar(value) -> np.ndarray | None:
    """
    Decode an scalar event
    :param value: A value field of an event
    :return: Decoded scalar
    """
    if value.HasField("simple_value"):
        return value.simple_value
    return None


def _get_image(value) -> np.ndarray | None:
    """
    Decode an image event
    :param value: A value field of an event
    :return: Decoded image
    """
    if value.HasField("image"):
        encoded_image = value.image.encoded_image_string
        return imageio.imread(encoded_image)
    return None


def _get_image_raw(value) -> np.ndarray | None:
    """
    Return raw image data
    :param value: A value field of an event
    :return: Raw image data
    """
    if value.HasField("image"):
        return value.image.encoded_image_string
    return None


class SummaryReader(Iterable):
    """
    Iterates over events in all the files in the current logdir.
    Only scalars and images are supported at the moment.
    """

    _DECODERS = {  # noqa: RUF012
        "scalar": _get_scalar,
        "image": _get_image,
        "image_raw": _get_image_raw,
    }

    def __init__(
        self,
        logdir: str | Path,
        tag_filter: Iterable | None = None,
        types: Iterable = ("scalar",),
        stop_on_error: bool = False,
    ):
        """
        Initalize new summary reader
        :param logdir: A directory with Tensorboard summary data
        :param tag_filter: A list of tags to leave (`None` for all)
        :param types: A list of types to get.
            Only 'scalar' and 'image' types are allowed at the moment.
        :param stop_on_error: Whether stop on a broken file
        """
        self._logdir = Path(logdir)

        self._tag_filter = set(tag_filter) if tag_filter is not None else None
        self._types = set(types)
        self._check_type_names()
        self._stop_on_error = stop_on_error

    def _check_type_names(self):
        if self._types is None:
            return
        if not all(type_name in self._DECODERS for type_name in self._types):
            raise ValueError("Invalid type name")

    def _decode_events(self, events: Iterable) -> Iterator[SummaryItem | None]:
        """
        Convert events to `SummaryItem` instances
        :param events: An iterable with events objects
        :return: A generator with decoded events
            or `None`s if an event can't be decoded
        """

        for event in events:
            if not event.HasField("summary"):
                yield None
            step = event.step
            wall_time = event.wall_time
            for value in event.summary.value:
                tag = value.tag
                for value_type in self._types:
                    decoder = self._DECODERS[value_type]
                    data = decoder(value)
                    if data is not None:
                        yield SummaryItem(
                            tag=tag,
                            step=step,
                            wall_time=wall_time,
                            value=data,
                            type=value_type,
                        )
                yield None

    def _check_tag(self, tag: str) -> bool:
        """
        Check if a tag matches the current tag filter
        :param tag: A string with tag
        :return: A boolean value.
        """
        return self._tag_filter is None or tag in self._tag_filter

    def _check_item(self, item):
        del item  # unused argument

    def __iter__(self) -> Iterator[SummaryItem]:
        """
        Iterate over events in all the files in the current logdir
        :return: A generator with `SummaryItem` objects
        """
        log_files = sorted(f for f in self._logdir.glob("*") if f.is_file())
        for file_path in log_files:
            with file_path.open("rb") as f:
                reader = EventsFileReader(f)
                try:
                    yield from (
                        item
                        for item in self._decode_events(reader)
                        if item is not None and all([self._check_tag(item.tag), item.type in self._types])
                    )
                except EventReadingError:
                    if self._stop_on_error:
                        raise
                    else:
                        continue
