import array
from queue import Queue, Empty, Full
from typing import Optional, List, Callable

import threading

import pyaudio
import pydub
import wave
import signal
import sys
import time
from io import BytesIO as StringIO

from pydub.utils import get_array_type
from soundmeter.settings import Config
from soundmeter.utils import noalsaerr, coroutine


from led_machine.percent import PercentGetter

RECORD_PERIOD_SECONDS = .15
DATA_KEEP_PERIOD_SECONDS = 45.0
MAX_SIZE = int(DATA_KEEP_PERIOD_SECONDS / RECORD_PERIOD_SECONDS)
AMBIENT_AMOUNT = 1600


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

                bit_depth = segment.sample_width * 8
                array_type = get_array_type(bit_depth)

                numeric_array = array.array(array_type, segment.raw_data)
                data_list = [a for a in numeric_array]
                inverted_frame_duration = len(data_list) / segment.duration_seconds
                # print(frame_duration)
                frequencies = []
                high = None
                steps = 0
                for level in data_list:
                    steps += 1
                    if high is None:
                        high = level > 0
                    next_high = level > -200 if high else level > 200
                    if high is not next_high:
                        # multiply steps by 2 because steps is half the distance between two high points
                        frequencies.append(inverted_frame_duration / (steps * 2))
                        steps = 0
                        high = next_high
                if frequencies and segment.rms > 6000:
                    frequency = sum(frequencies) // len(frequencies)
                    print(frequency)

                self.meter(rms)

        except self.__class__.StopException:
            pass

    def meter(self, rms):
        sys.stdout.write('\r%10d  ' % rms)
        sys.stdout.flush()


class MyMeter(MeterBase):
    def __init__(self):
        super().__init__()
        self.queue = Queue(100)

    def meter(self, rms):
        try:
            self.queue.put_nowait(rms)
        except Full:
            pass


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
        self.data: List[int] = [1000] * MAX_SIZE
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
        # Almost all of the time we're only going to pop 0 or 1 values, but if this isn't updated in a while, then
        #   we may have to update a bunch
        while True:
            value = self.pop_value()
            if value is None:
                break
            self.data.append(value)
            self.data.pop(0)

    def average_over(self, my_slice: slice) -> Optional[float]:
        data = self.data[my_slice]
        return sum(data) / len(data)

    def percent_over_seconds(self, seconds: float):
        now = self.get_current_value()
        low_data = single_reduce(self.data[get_slice_for_time(-seconds)], min)
        low_normal = sum(low_data) / len(low_data)
        diff = now - low_normal - AMBIENT_AMOUNT
        whole_diff = diff / (seconds * 100 + 9000)
        return max(0.0, min(1.0, .3 + whole_diff))

    def get_volume_percent(self):
        now = self.get_current_value() - AMBIENT_AMOUNT
        return max(0.0, min(1.0, now / 20000))

    def get_relative_percent(self):
        return self.percent_over_seconds(20) * .3 + self.percent_over_seconds(10) * .1 + self.percent_over_seconds(5) * .2 + self.percent_over_seconds(3) * .3 + self.percent_over_seconds(1) * .1


class VolumePercentGetter(PercentGetter):
    def __init__(self, helper: MeterHelper):
        self.helper = helper

    def get_percent(self, seconds: float) -> float:
        self.helper.update()
        volume_percent = self.helper.get_volume_percent()
        relative_percent = self.helper.get_relative_percent()
        percent = (volume_percent ** 2.0) * .6 + relative_percent * .4
        return percent


def main():
    helper = MeterHelper()
    helper.start()
    percent_getter = VolumePercentGetter(helper)
    while True:
        percent = percent_getter.get_percent(0.0)
        bars = int(100 * percent)
        total_space = 100 - bars
        left_space = total_space // 2
        right_space = total_space - left_space
        print(" " * left_space + "|" * bars + " " * right_space + ">")
        time.sleep(0.06)


if __name__ == '__main__':
    main()
