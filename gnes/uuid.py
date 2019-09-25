import threading
import time
from datetime import datetime

from . import helper


@helper.Singleton
class BaseIDGenerator(object):
    """
    Thread-safe (auto incremental) uuid generator
    """

    def __init__(self, start_id: int = 0, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self._lock = threading.Lock()
        self._next_id = start_id

    def reset(self, start_id: int = 0):
        with self._lock:
            self._next_id = start_id

    def next(self) -> int:
        with self._lock:
            temp = self._next_id
            self._next_id += 1
            return temp


@helper.Singleton
class SnowflakeIDGenerator(object):

    def __init__(self,
                 machine_id: int = 0,
                 datacenter_id: int = 0,
                 *args,
                 **kwargs):
        self._lock = threading.Lock()
        self._next_id = 0

        self.machine_id = machine_id
        self.datacenter_id = datacenter_id

        self.machine_bits = 5
        self.datacenter_bits = 5
        self.max_machine_id = -1 ^ -1 << self.machine_bits
        self.max_datacenter_id = -1 ^ (-1 << self.datacenter_bits)

        self.counter_bits = 12
        self.max_counter_mask = -1 ^ -1 << self.counter_bits

        self.machine_shift = self.counter_bits
        self.datacenter_shift = self.counter_bits + self.machine_bits
        self.timestamp_shift = self.counter_bits + self.machine_bits + self.datacenter_bits

        self.twepoch = int(time.mktime(time.strptime('2019-01-01 00:00:00', "%Y-%m-%d %H:%M:%S")))
        self.last_timestamp = -1
        self.current_timestamp = lambda: int(datetime.now().timestamp() * 1000)

    # def _get_timestamp(self) -> int:
    #     return int(datetime.now().timestamp() * 1000)

    def _get_next_timestamp(self, last_timestamp) -> int:
        timestamp = self.current_timestamp()
        while timestamp <= last_timestamp:
            timestamp = self.current_timestamp()
        return timestamp

    def next(self) -> int:
        with self._lock:
            timestamp = self.current_timestamp()
            if self.last_timestamp == timestamp:
                self._next_id = (self._next_id + 1) & self.max_counter_mask
                if self._next_id == 0:
                    timestamp = self._get_next_timestamp(self.last_timestamp)
            else:
                self._next_id = 0

            if timestamp < self.last_timestamp:
                raise ValueError(
                    'the current timestamp is smaller than the last timestamp')

            self.last_timestamp = timestamp
            uuid = ((timestamp - self.twepoch) << self.timestamp_shift) \
                    | (self.datacenter_id << self.datacenter_shift) \
                    | (self.machine_id << self.machine_shift) \
                    | self._next_id
            return uuid
