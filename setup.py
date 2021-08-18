from setuptools import setup, find_packages

setup(
    name="led-machine",
    version="0.1",
    packages=find_packages(),
    author="retrodaredevil",
    author_email="retrodaredevil@gmail.com",
    description="Manages LEDs",
    url="https://github.com/retrodaredevil/led-machine",
    entry_points={"console_scripts": ["led-machine = led_machine:main",
                                      ]},
    install_requires=["adafruit-circuitpython-neopixel",
                      "slack_sdk",
                      "soundmeter",
                      ]
)
