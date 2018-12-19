#!/usr/bin/env python3

from webthing import (Action, Event, SingleThing, Property, Thing, Value, WebThingServer)

import logging
import time
import uuid
import os
import subprocess

import RPi.GPIO as GPIO

def Shutdown(channel): 
  print ("shutting down ...")
  os.system("sudo shutdown -h now") 


HOME_DIR = os.getenv("SYNCHRONIZED_LIGHTS_HOME")

class LightShowThing(Thing):
    """ LightShowPI Thing """

    def __init__(self):
        Thing.__init__(self, 'LighShowPI', [], 'A web connected LightShowPI controller')

        self.on = False
        self.music = False
        self.turn_off()

        self.add_property(
            Property(self,
                 'on',
                 Value(self.get_onoff, self.set_onoff),
                 metadata={
                     '@type': 'OnOffProperty',
                     'label': 'On/Off',
                     'type': 'boolean',
                     'description': 'Whether the lights are turned on',
                 }))
        self.add_property(
            Property(self,
                 'music',
                 Value(self.get_music, self.set_music),
                 metadata={
                     '@type': 'BooleanProperty',
                     'label': 'React To Music',
                     'type': 'boolean',
                     'description': 'React to Music or not',
                 }))


    def get_onoff(self):
        return self.on

    def set_onoff(self, onoff):
        if self.on == onoff:
            return

        self.on = onoff
        if self.on:
            self.turn_on()
        else:
            self.turn_off()

    def get_music(self):
        return self.music

    def set_music(self, onoff):
        if self.music == onoff:
            return

        self.music = onoff
        if self.on == False:
            return

        if self.music:
            self.start_music()
        else:
            self.stop_music()

    def turn_on(self):
        if self.music:
            self.start_music()
        else:
            os.system('pkill -f "bash $SYNCHRONIZED_LIGHTS_HOME/bin"')
            os.system('pkill -f "python $SYNCHRONIZED_LIGHTS_HOME/py"')
            os.system("python ${SYNCHRONIZED_LIGHTS_HOME}/py/hardware_controller.py --state=on")

    def turn_off(self):
        os.system('pkill -f "bash $SYNCHRONIZED_LIGHTS_HOME/bin"')
        os.system('pkill -f "python $SYNCHRONIZED_LIGHTS_HOME/py"')
        os.system("python ${SYNCHRONIZED_LIGHTS_HOME}/py/hardware_controller.py --state=off")

    def start_music(self):
        if self.on == False:
            return;

        os.system('pkill -f "bash $SYNCHRONIZED_LIGHTS_HOME/bin"')
        os.system('pkill -f "python $SYNCHRONIZED_LIGHTS_HOME/py"')

        os.system('amixer set Speaker playback 90%')

        os.system("${SYNCHRONIZED_LIGHTS_HOME}/bin/play_sms &")
        os.system("${SYNCHRONIZED_LIGHTS_HOME}/bin/check_sms &")

    def stop_music(self):
        if self.on:
            self.turn_on()
        else:
            self.turn_off()


def run_server():
    thing = LightShowThing()
    thing.set_property('on', True)
    thing.turn_on()
    thing.set_property('music', False)

    # In the single thing case, the thing's name will be broadcast.
    server = WebThingServer(SingleThing(thing), port=8888)
    try:
        logging.info('starting the server')
        server.start()
    except KeyboardInterrupt:
        logging.info('stopping the server')
        server.stop()
        logging.info('done')


if __name__ == '__main__':
    logging.basicConfig(
        level=10,
        format="%(asctime)s %(filename)s:%(lineno)s %(levelname)s %(message)s"
    )
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(14,GPIO.OUT)
    GPIO.output(14,GPIO.HIGH)

    print ("setting led on")
    GPIO.setup(21, GPIO.IN, pull_up_down = GPIO.PUD_UP)  

    # Add our function to execute when the button pressed event happens 
    GPIO.add_event_detect(21, GPIO.FALLING, callback = Shutdown, bouncetime = 2000)  

    run_server()
