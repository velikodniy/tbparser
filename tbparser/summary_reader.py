from collections import namedtuple
from collections.abc import Iterable
from pathlib import Path
from typing import Union, Optional

import imageio
import numpy as np

from tbparser.events_reader import EventReadingError, EventsFileReader

SummaryItem = namedtuple(
    'SummaryItem', ['tag', 'step', 'wall_time', 'value', 'type']
)


def _get_scalar(value) -> Optional[np.ndarray]:
    """
    Decode an scalar event
    :param value: A value field of an event
    :return: Decoded scalar
    """
    if value.HasField('simple_value'):
        return value.simple_value
    return None


def _get_image(value) -> Optional[np.ndarray]:
    """
    Decode an image event
    :param value: A value field of an event
    :return: Decoded image
    """
    if value.HasField('image'):
        encoded_image = value.image.encoded_image_string
        data = imageio.imread(encoded_image)
        return data
    return None


def _get_image_raw(value) -> Optional[np.ndarray]:
    """
    Return raw image data
    :param value: A value field of an event
    :return: Raw image data
    """
    if value.HasField('image'):
        return value.image.encoded_image_string
    return None


class SummaryReader(Iterable):
    """
    Iterates over events in all the files in the current logdir.
    Only scalars and images are supported at the moment.
    """

    _DECODERS = {
        'scalar': _get_scalar,
        'image': _get_image,
        'image_raw': _get_image_raw,
    }

    def __init__(
            self,
            logdir: Union[str, Path],
            tag_filter: Optional[Iterable] = None,
            types: Iterable = ('scalar',),
            stop_on_error: bool = False
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
        if not all(
                type_name in self._DECODERS.keys() for type_name in self._types
        ):
            raise ValueError('Invalid type name')

    def _decode_events(self, events: Iterable) -> Optional[SummaryItem]:
        """
        Convert events to `SummaryItem` instances
        :param events: An iterable with events objects
        :return: A generator with decoded events
            or `None`s if an event can't be decoded
        """

        for event in events:
            if not event.HasField('summary'):
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
                            type=value_type
                        )
                else:
                    yield None

    def _check_tag(self, tag: str) -> bool:
        """
        Check if a tag matches the current tag filter
        :param tag: A string with tag
        :return: A boolean value.
        """
        return self._tag_filter is None or tag in self._tag_filter

    def _check_item(self, item):
        return

    def __iter__(self) -> SummaryItem:
        """
        Iterate over events in all the files in the current logdir
        :return: A generator with `SummaryItem` objects
        """
        log_files = sorted(f for f in self._logdir.glob('*') if f.is_file())
        for file_path in log_files:
            with open(file_path, 'rb') as f:
                reader = EventsFileReader(f)
                try:
                    yield from (
                        item for item in self._decode_events(reader)
                        if item is not None and all([
                            self._check_tag(item.tag),
                            item.type in self._types
                        ])
                    )
                except EventReadingError:
                    if not self._stop_on_error:
                        raise
                    else:
                        continue
