import asyncio
import time
from asyncio import Future
from typing import Optional

from slack import WebClient
from slack.web.slack_response import SlackResponse


class SlackHelper:
    def __init__(self, token, channel):
        self.channel = channel
        self.client = WebClient(token=token, run_async=True)
        self.future: Optional[Future] = None
        self.last_message_time: Optional[float] = None
        self.last_request: Optional[float] = None

    def update(self):
        seconds = time.time()
        if self.last_request is None or self.last_request + 2.5 < seconds:
            if self.future is not None:
                self.future.cancel()
            self.last_request = seconds
            self.future = self.client.conversations_history(channel=self.channel)

            # Yeah, I totally copied some of this: https://stackoverflow.com/a/325528/5434860
            def loop_in_thread(loop):
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.future)

            event_loop = asyncio.get_event_loop()
            import threading
            thread = threading.Thread(target=loop_in_thread, args=(event_loop,))
            thread.start()

            if self.last_message_time is None:
                self.last_message_time = seconds

    def new_messages(self) -> list:
        if self.future is not None:
            if self.future.done():
                result: SlackResponse = self.future.result()
                self.future = None
                messages = list(result["messages"])  # get messages and copy it

                if self.last_message_time:
                    for i in range(len(messages) - 1, -1, -1):
                        message = messages[i]
                        timestamp = float(message["ts"])
                        if timestamp <= self.last_message_time:
                            messages.pop(i)

                if messages:
                    return_nothing = self.last_message_time is None
                    self.last_message_time = float(messages[0]["ts"])
                    if return_nothing:
                        return []

                return messages

        return []

