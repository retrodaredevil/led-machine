from queue import Queue

from slack_sdk.rtm.v2 import RTMClient


class SlackHelper:
    def __init__(self, token, channel):
        self.channel = channel
        self.client = RTMClient(token=token)
        self.message_queue = Queue()

        from threading import Thread
        thread = Thread(target=self.client.start)
        thread.start()

        @self.client.on("message")
        def receive_message(client: RTMClient, message: dict):
            self.message_queue.put(message)

    def __del__(self):
        self.client.close()

    def update(self):
        pass

    def new_messages(self) -> list:
        messages = []
        while not self.message_queue.empty():
            messages.append(self.message_queue.get())

        return messages

