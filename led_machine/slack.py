from queue import Queue
from typing import Optional
from urllib.error import URLError
import time

from slack_sdk import WebClient
from slack_sdk.socket_mode import SocketModeClient
# https://slack.dev/python-slack-sdk/socket-mode/index.html
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse


class SlackHelper:
    def __init__(self, bot_token, app_token, channel):
        self.bot_token = bot_token
        self.app_token = app_token
        self.channel = channel
        self.message_queue = Queue()
        self.last_connect_try: Optional[float] = None

        print("Initializing SlackHelper")
        self.socket_client = SocketModeClient(
            app_token=self.app_token,
            web_client=WebClient(token=self.bot_token)
        )
        self.socket_client.socket_mode_request_listeners.append(lambda client, req: self._process_event(client, req))
        self.check_connected()
        print("Finished initializing SlackHelper")

    def __del__(self):
        self.socket_client.close()

    def check_connected(self):
        if not self.socket_client.is_connected():
            now = time.time()
            if self.last_connect_try is not None and self.last_connect_try + 10 > now:
                return  # We've tried in the last 10 seconds
            print("Going to try to connect")
            self.last_connect_try = now
            try:
                self.socket_client.connect()
                print("Connected")
            except URLError:
                print("Could not connect")

    def _process_event(self, client: SocketModeClient, req: SocketModeRequest):
        if req.type == "events_api":
            # Acknowledge the request anyway
            response = SocketModeResponse(envelope_id=req.envelope_id)
            client.send_socket_mode_response(response)

            # Add a reaction to the message if it's a new message
            message = req.payload["event"]
            if message["type"] == "message" and message.get("subtype") is None:
                self.message_queue.put(message)
                # This doesn't work for some reason
                # print(client.web_client.reactions_add(
                #     name="eyes",
                #     channel=message["channel"],
                #     timestamp=message["ts"],
                # ))

    def new_messages(self) -> list:
        self.check_connected()  # We don't really care if this blocks
        messages = []
        while not self.message_queue.empty():
            messages.append(self.message_queue.get())
        return messages

