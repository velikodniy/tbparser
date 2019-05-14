import struct
from crc32c import crc32 as crc32c
from typing import Iterable, BinaryIO, Optional

from tensorboard.compat.proto.event_pb2 import Event


def _u32(x):
    return x & 0xffffffff


def _masked_crc32c(data):
    x = _u32(crc32c(data))
    return _u32(((x >> 15) | _u32(x << 17)) + 0xa282ead8)


class EventReadingError(Exception):
    """
    An exception that correspond to an event file reading error
    """
    pass


class EventsFileReader(Iterable):
    """
    An iterator over a Tensorboard events file
    """

    def __init__(self, events_file: BinaryIO):
        """
        Initialize an iterator over an events file

        :param events_file: An opened file-like object.
        """
        self._events_file = events_file

    def _read(self, size: int) -> Optional[bytes]:
        """
        Read exactly next `size` bytes from the current stream.

        :param size: A size in bytes to be read.
        :return: A `bytes` object with read data or `None` on EOF.
        :except: NotImplementedError if the stream is in non-blocking mode.
        :except: EventReadingError on reading error.
        """
        data = self._events_file.read(size)
        if data is None:
            raise NotImplementedError(
                'Reading of a stream in non-blocking mode'
            )
        if 0 < len(data) < size:
            raise EventReadingError(
                'The size of read data is less than requested size'
            )
        if len(data) == 0:
            return None
        return data

    def _read_and_check(self, size: int) -> Optional[bytes]:
        """
        Read and check data described by a format string.

        :param size: A size in bytes to be read.
        :return: A decoded number.
        :except: NotImplementedError if the stream is in non-blocking mode.
        :except: EventReadingError on reading error.
        """
        data = self._read(size)
        if data is None:
            return None
        checksum_size = struct.calcsize('I')
        checksum = struct.unpack('I', self._read(checksum_size))[0]
        checksum_computed = _masked_crc32c(data)
        if checksum != checksum_computed:
            raise EventReadingError(
                'Invalid checksum. {checksum} != {crc32}'.format(
                    checksum=checksum, crc32=checksum_computed
                )
            )
        return data

    def __iter__(self) -> Event:
        """
        Iterates over events in the current events file

        :return: An Event object
        :except: NotImplementedError if the stream is in non-blocking mode.
        :except: EventReadingError on reading error.
        """
        while True:
            header_size = struct.calcsize('Q')
            header = self._read_and_check(header_size)
            if header is None:
                break
            event_size = struct.unpack('Q', header)[0]
            event_raw = self._read_and_check(event_size)
            if event_raw is None:
                raise EventReadingError('Unexpected end of events file')
            event = Event()
            event.ParseFromString(event_raw)
            yield event
