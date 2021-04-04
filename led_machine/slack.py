from queue import Queue

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

        self.socket_client = SocketModeClient(
            app_token=self.app_token,
            web_client=WebClient(token=self.bot_token)
        )
        self.socket_client.socket_mode_request_listeners.append(lambda client, req: self._process_event(client, req))
        self.socket_client.connect()

    def __del__(self):
        self.socket_client.close()

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
        messages = []
        while not self.message_queue.empty():
            messages.append(self.message_queue.get())
        return messages

