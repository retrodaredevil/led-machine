# led-machine
The goal of this is to support WS2812B individual addressable LEDs.


### Installing to Machine:
Installing NEOPixel library:
```shell
sudo pip3 install rpi_ws281x adafruit-circuitpython-neopixel
```
Installing LED Machine:
```shell
sudo python3 setup.py install
```

### Links
* https://www.amazon.com/dp/B0892YF143
* https://tutorials-raspberrypi.com/connect-control-raspberry-pi-ws2812-rgb-led-strips/


https://pinout.xyz

### Slack
This uses Slack's [event api](https://api.slack.com/apis/connections/events-api#subscriptions) and uses Socket mode.

You must enable Socket mode then enable Events

Slack bot events to sub to:
```
message.channels
```

Scopes to have:
```
reactions:write
```

## Install systmed service
Copy `led-machine.service` to `/etc/systemd/system/`



### Technical

#### Mypy checking

Run:
```shell
mypy led_machine
```

```shell
pi@raspberrypi:~/led-machine $ sudo systemctl daemon-reload
pi@raspberrypi:~/led-machine $ sudo systemctl enable led-machine
Created symlink /etc/systemd/system/multi-user.target.wants/led-machine.service → /etc/systemd/system/led-machine.service.
pi@raspberrypi:~/led-machine $ sudo systemctl start led-machine
```



### Ideas:
```
fast rainbow; slow carnival // effectively two messages being sent in one
blue green red  // fades between colors
blue green red | red // half blue green red, half only red
offset window; blue green red | red // blue green red starts using the "window" offset, then other half is only red
offset window; blue green red 30% | red // start on "window" offset, first 30% is blue green red, other 70% is only red
offset window; blue green red 30p | red // start on "window" offset, first 30 pixels is blue green red, other pixels is only red
lamp josh // turns on a certain set of pixels to white
blue green red | red ~ purple ~ blue purple // Split on "~". For each setting, fade between them
```
