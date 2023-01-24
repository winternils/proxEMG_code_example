import json
import time 
import sys

from matplotlib.pyplot import text

import pygame as pg
from pygame.locals import *

from MIDI_LSL import MIDI_LSL
from MIDI import MIDI

from rtmidi.midiutil import open_midiinput

from volume_control import get_current_volume

class proxEMGExperiment:

    def __init__(self) -> None:
        self.midi = MIDI()
        self.lsl = MIDI_LSL('MIDI')
        self.markers = json.load(open('/Users/work/Desktop/Nils/proxEMG/code/proxEMG/experiment_lsl_markers.json', 'r'))
        # self.lsl.send(self.markers['create'],1)

        self.midi.open_port(0)

    def init_midiin(self):
        # Prompts user for MIDI input port, unless a valid port number or name
        # is given as the first argument on the command line.
        # API backend defaults to ALSA on Linux.
        port = sys.argv[1] if len(sys.argv) > 1 else None
        try:
            self.midiin, self.port_name = open_midiinput(port)
        except (EOFError, KeyboardInterrupt):
            sys.exit()

    def init_screen(self):
        info = pg.display.Info()
        # self.screen = pg.display.set_mode((info.current_w, info.current_h), pg.FULLSCREEN)
        self.screen = pg.display.set_mode((info.current_w, info.current_h), pg.RESIZABLE)
        self.screen.fill((240, 240, 240))
        self.screen_rect = self.screen.get_rect()

    def init_txt(self):
        self.font = pg.font.Font(None, 45)

    def instruct(self, text, col):

        self.screen.fill((240, 240, 240))
        txt = self.font.render(text, True, col)
        self.screen.blit(txt, txt.get_rect(center=self.screen_rect.center))
        # self.wait()
        pg.display.flip()

    def test_midi_in(self):
        print("Entering main loop. Press Escape to exit.")
        
        self.init_screen()
        self.init_txt()

        # training
        col = (0,0,0)
        gesture_instruction = "gesture training - please read the instructions carefully! Start with first gesture."
        turning_instruction = "turning training - please read the instructions carefully! Press enter to continue."
        pause_instruction = "Congratulations - the first part of training is done! Press enter to continue."

        # self.instruct(gesture_instruction, col)

        instructions = [gesture_instruction, pause_instruction, turning_instruction]

        # defaults
        instruction = ""
        direction = "right"
        trial_start = True
        trial_end_right = False
        trial_end_left = False
        gesture_turning_switch = False

        # settings
        gesture_counter = 0;
        num_gesture_required = 50;
        rotation_counter = 0;
        num_rotation_required = 50;
        instruction_cnt = 0;
        
        while True:

            for event in pg.event.get():

                if gesture_counter < num_gesture_required:
                    
                    if event.type == pg.KEYDOWN:
                        if event.key == pg.K_ESCAPE:
                        
                            self.lsl.send(self.markers['end'],1)
                            self.midiin.close_port()
                            del self.midiin
                            self.close()
                        
                        if event.key == pg.K_SPACE:
                            self.lsl.send("gesture:start",1)

                    if event.type == pg.KEYUP:
                        if event.key == pg.K_SPACE:
                            self.lsl.send("gesture:end",1)
                            gesture_counter += 1

                if gesture_counter == num_gesture_required:
                    instruction_cnt = 1

                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_RETURN:
                        gesture_counter += 1
                        instruction_cnt += 1
                        if instruction_cnt > 2:
                            gesture_turning_switch = True

                if instruction_cnt <= 2:
                    self.instruct(instructions[instruction_cnt], col)

            if rotation_counter == num_rotation_required:
                col = (0,0,0)
                gesture_turning_switch = False
                knob = 50
                txt = "Congratulations - the training is completed!"
                self.instruct(txt, col)
            
            if gesture_turning_switch:
                # msg = self.midiin.get_message()

                knob = get_current_volume()

                # if msg:

                #     message, deltatime = msg
                #     self.lsl.send(message,1)
                #     #timer += deltatime

                #     # print("[%s] @%0.6f %r" % (self.port_name, timer, message))
                #     self.midi.send_to_port(message)
                #     self.lsl.send(message,0)

                # knob = message[2]
                if knob > 80:
                    col = (220,20,60)
                    instruction = "  <-  turn down the volume until < 20"

                    if trial_end_right is True:
                        marker = "move:end;direction:"+direction+";"
                        self.lsl.send(str(marker),1)
                        rotation_counter += .5
                        trial_end_right = False
                        trial_end_left = True

                        direction = "left"
                        trial_start = True

                elif knob < 20:
                    col = (0,128,0)
                    instruction = "  ->  turn up the volume until > 80"
                    
                    if trial_end_left is True:
                        marker = "move:end;direction:"+direction+";"
                        self.lsl.send(str(marker),1)
                        rotation_counter += .5
                        trial_end_right = True
                        trial_end_left = False
                        
                        direction = "right"
                        trial_start = True

                else:
                    col = (0,0,0)

                    if trial_start == True:

                        marker = "move:start;direction:"+direction+";"
                        self.lsl.send(str(marker),1)
                        trial_start = False

                        if direction == "left":
                            trial_end_left = True
                        elif direction == "right":
                            trial_end_right = True

                txt = str(knob)+instruction
                self.instruct(txt, col)

    def new_method(self):
        num_gesture_required = 20;
        return num_gesture_required

pg.init()
exp = proxEMGExperiment()
# exp.init_midiin()
exp.test_midi_in()