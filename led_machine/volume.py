import time
from queue import Queue, Empty
from typing import Optional, List, Callable

import threading

import pyaudio
import pydub
import wave
import signal
import sys
import time
from io import BytesIO as StringIO
from soundmeter.settings import Config
from soundmeter.utils import noalsaerr, coroutine

RECORD_PERIOD_SECONDS = .15
DATA_KEEP_PERIOD_SECONDS = 45.0
MAX_SIZE = int(DATA_KEEP_PERIOD_SECONDS / RECORD_PERIOD_SECONDS)


class MeterBase:
    """
    This class copy-pasted from https://github.com/shichao-an/soundmeter/blob/master/soundmeter/meter.py

    It could not be used directly because it tries to handle SIGINT when you import it for some dumb reason
    """

    class StopException(Exception):
        pass

    def __init__(self, seconds=None,
                 num=None, script=None, log=None,
                 verbose=False, segment=None, profile=None, *args, **kwargs):
        self.config = Config(profile)
        self.output = StringIO()
        with noalsaerr():
            self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(
            format=self.config.FORMAT,
            channels=self.config.CHANNELS,
            input_device_index=self.config.INPUT_DEVICE_INDEX,
            input=True,
            rate=self.config.RATE,
            frames_per_buffer=self.config.FRAMES_PER_BUFFER)
        self.seconds = seconds
        self.num = num
        self.script = script
        self.log = log
        self.verbose = verbose
        self.segment = segment
        self._timeout = False
        self._timer = None
        self._data = {}

    @coroutine
    def record(self):
        """
        Record PyAudio stream into StringIO output

        This coroutine keeps stream open; the stream is closed in stop()
        """

        while True:
            frames = []
            self.stream.start_stream()
            for i in range(self.num_frames):
                data = self.stream.read(self.config.FRAMES_PER_BUFFER)
                frames.append(data)
            self.output.seek(0)
            w = wave.open(self.output, 'wb')
            w.setnchannels(self.config.CHANNELS)
            w.setsampwidth(self.audio.get_sample_size(self.config.FORMAT))
            w.setframerate(self.config.RATE)
            w.writeframes(b''.join(frames))
            w.close()
            yield

    def start(self):
        segment = self.segment or self.config.AUDIO_SEGMENT_LENGTH
        self.num_frames = int(
            self.config.RATE / self.config.FRAMES_PER_BUFFER * segment)
        if self.seconds:
            signal.setitimer(signal.ITIMER_REAL, self.seconds)
        if self.verbose:
            self._timer = time.time()

        try:
            record = self.record()
            while True:
                record.send(True)  # Record stream `AUDIO_SEGMENT_LENGTH' long
                data = self.output.getvalue()
                segment = pydub.AudioSegment(data)
                rms = segment.rms
                self.meter(rms)

        except self.__class__.StopException:
            pass

    def meter(self, rms):
        sys.stdout.write('\r%10d  ' % rms)
        sys.stdout.flush()


class MyMeter(MeterBase):
    def __init__(self):
        super().__init__()
        self.queue = Queue()

    def meter(self, rms):
        self.queue.put(rms)


def single_reduce(data: List[int], chooser: Callable[[int, int], int]) -> List[int]:
    length = len(data) // 2
    r = []
    for i in range(length):
        a = data[i * 2]
        b = data[i * 2 + 1]
        value = chooser(a, b)
        r.append(value)
    return r


def get_slice_for_time(seconds_ago_start: float, seconds_ago_end: float = 0.0):
    """
    :param seconds_ago_start: A positive decimal value representing how many seconds ago to start
    :param seconds_ago_end: A positive decimal value representing how many seconds ago to end
    :return: A slice to use on a list of values spaced RECORD_PERIOD_SECONDS apart
    """
    start_index = -int(seconds_ago_start / RECORD_PERIOD_SECONDS)
    end_index = -int(seconds_ago_end / RECORD_PERIOD_SECONDS)
    if start_index == 0:
        start_index = -1
    if end_index == 0:
        end_index = None
    return slice(start_index, end_index)


class MeterHelper:
    def __init__(self):

        self.meter = MyMeter()
        self.meter.config.AUDIO_SEGMENT_LENGTH = RECORD_PERIOD_SECONDS
        self.thread = threading.Thread(target=lambda: self.__do_run(), args=())
        self.thread.daemon = True
        self.data: List[int] = []
        self.next_index: int = 0

    def start(self):
        self.thread.start()

    def __do_run(self):
        print("Starting run")
        self.meter.start()
        print("Ended run")

    def pop_value(self) -> Optional[int]:
        try:
            return self.meter.queue.get_nowait()
        except Empty:
            return None

    def get_current_value(self) -> Optional[int]:
        return self.data[-1] if self.data else None

    def update(self):
        value = self.pop_value()
        if value is not None:
            self.data.append(value)
            while len(self.data) > MAX_SIZE:
                self.data.pop(0)

    def average_over(self, my_slice: slice) -> Optional[float]:
        if not self.data:
            return None
        data = self.data[my_slice]
        return sum(data) / len(data)

    def percent_over_seconds(self, seconds: float):
        now = self.get_current_value()
        if now is None:
            return None
        low_data = single_reduce(self.data[get_slice_for_time(-seconds)], min)
        if not low_data:
            return None
        low_normal = sum(low_data) / len(low_data)
        diff = now - low_normal
        whole_diff = diff / (seconds * 100 + 9000)
        return max(0.0, min(1.0, .5 + whole_diff))

    def get_volume_percent(self):
        now = self.get_current_value()
        if now is None:
            return None
        return max(0.0, min(1.0, now / 20000))

    def get_relative_percent(self):
        now = self.get_current_value()
        if now is None:
            return None
        first = self.percent_over_seconds(20)
        if first is None:
            return None

        return first * .3 + self.percent_over_seconds(10) * .1 + self.percent_over_seconds(5) * .2 + self.percent_over_seconds(3) * .3 + self.percent_over_seconds(1) * .1


ORIGINAL = ((30, .5), (10, .2), (3, .2), (1, .1))


def main():
    helper = MeterHelper()
    helper.start()
    while True:
        helper.update()
        volume_percent = helper.get_volume_percent()
        relative_percent = helper.get_relative_percent()
        if volume_percent is not None and relative_percent is not None:
            percent = volume_percent * .25 + relative_percent * .75
            bars = int(100 * percent)
            print("|" * bars + " " * (100 - bars) + ">")
        time.sleep(0.06)


if __name__ == '__main__':
    main()
