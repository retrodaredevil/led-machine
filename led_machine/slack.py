import asyncio
import time
from asyncio import Future
from typing import Optional

from slack import WebClient
from slack.web.slack_response import SlackResponse

from concurrent.futures import ThreadPoolExecutor


class SlackHelper:
    def __init__(self, token, channel):
        self.channel = channel
        self.client = WebClient(token=token, run_async=True)
        self.future: Optional[Future] = None
        self.last_message_time: Optional[float] = None
        self.last_request: Optional[float] = None
        self.last_cancel = None
        self.executor = ThreadPoolExecutor(1)

    def __del__(self):
        self.executor.shutdown()

    def update(self):
        seconds = time.time()
        if (self.last_request is None or (self.last_request + 2.5 < seconds
                                          and self.future is not None and self.future.done())
                or self.last_request + 7.0 < seconds):
            if self.future is not None:
                self.future.cancel()
                self.future = None
                self.last_cancel = seconds
            self.last_request = seconds
            if self.last_cancel is not None and self.last_cancel + 3.0 > seconds:  # We've cancelled recently, so give it some time
                return
            # This has tier 3 applied to it: https://api.slack.com/docs/rate-limits
            # https://api.slack.com/methods/conversations.history
            self.future = self.client.conversations_history(channel=self.channel, oldest=seconds - 300.0, limit=10)

            # Yeah, I totally copied some of this: https://stackoverflow.com/a/325528/5434860
            def loop_in_thread(loop):
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.future)

            event_loop = asyncio.get_event_loop()
            self.executor.submit(loop_in_thread, (event_loop,))

            if self.last_message_time is None:
                self.last_message_time = seconds

    def new_messages(self) -> list:
        if self.future is not None:
            if self.future.done():
                result: SlackResponse = self.future.result()
                self.future = None
                messages = result["messages"][::-1]  # get messages and copy+reverse it
                # After reversal, oldest messages are first

                if self.last_message_time:
                    for i in range(len(messages) - 1, -1, -1):
                        message = messages[i]
                        timestamp = float(message["ts"])
                        if timestamp <= self.last_message_time:
                            messages.pop(i)

                if messages:
                    return_nothing = self.last_message_time is None
                    self.last_message_time = float(messages[-1]["ts"])
                    if return_nothing:
                        return []

                return messages

        return []

