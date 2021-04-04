# led-machine
The goal of this is to support WS2812B individual addressable LEDs.

https://www.amazon.com/dp/B0892YF143

https://tutorials-raspberrypi.com/connect-control-raspberry-pi-ws2812-rgb-led-strips/

Installing NEOPixel library:
```shell
sudo pip3 install rpi_ws281x adafruit-circuitpython-neopixel
```

https://pinout.xyz

### Slack
This uses Slack's [event api](https://api.slack.com/apis/connections/events-api#subscriptions) and uses Socket mode.

You must enable Socket mode then enable Events

Slack bot events to sub to:
```
message.channels
```
