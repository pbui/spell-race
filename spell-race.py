#!/usr/bin/env pgzrun

''' Spell Race '''

from enum import IntEnum
from glob import glob

import os
import random
import subprocess

import pygame

# Configuration

WIDTH  = 1024
HEIGHT = 768

FRAMES_PER_SECOND = 60

WORDS = [l.strip() for l in open('words.txt')]

# Classes

class Dino(Actor):

    class State(IntEnum):
        Idle = 0
        Move = 1
        Kick = 2

    def __init__(self, color, *args, **kwargs):
        Actor.__init__(self, f'{color}_idle_0', *args, **kwargs)
        self.color       = color
        self.state       = Dino.State.Idle
        self.animation   = None
        self.flip        = False
        self.image_lists = (
            [os.path.basename(f) for f in sorted(glob(f'images/{color}_idle_*.png'))],
            [os.path.basename(f) for f in sorted(glob(f'images/{color}_move_*.png'))],
            [os.path.basename(f) for f in sorted(glob(f'images/{color}_kick_*.png'))],
        )

    def _transform(self, new_width, new_heigth):
        self._surf = pygame.transform.scale(self._surf, (new_width, new_heigth))
        if self.flip:
            self._surf = pygame.transform.flip(self._surf, self.flip, False)
        self._update_pos()

    def update(self, frame_number):
        image_list = self.image_lists[self.state]

        # Note: 2 is a multiplier to speedup animation
        self.image = image_list[
            int(2 * frame_number / FRAMES_PER_SECOND * len(image_list)) % len(image_list)
        ]

        self._transform(96, 96)

    def update_state(self, state):
        self.state = state

    def idle(self):
        self.update_state(Dino.State.Idle)

    def move(self, dx, dy, first=True):
        if first:
            self.update_state(Dino.State.Move)

        if dx:
            self.flip = dx < 0

        if self.state == Dino.State.Move:
            self.animate(
                duration    = 0.1,
                pos         = (self.pos[0] + dx * 5, self.pos[1] + dy * 5),
                on_finished = lambda: self.move(dx, dy, False)
            )

    def kick(self):
        self.update_state(Dino.State.Kick)
        self.animate(on_finished = lambda: self.update_state(Dino.State.Idle))

    def animate(self, *args, **kwargs):
        if self.animation and self.animation.running:
            self.animation.stop()

        self.animation = animate(self, *args, **kwargs)

class Game(object):
    dino         = Dino('blue', center=(WIDTH//16, HEIGHT//2))
    target       = None
    source       = ''
    clock        = 0
    frame_number = 0

# Drawing

def draw():
    screen.clear()
    screen.fill('green')
    screen.draw.filled_rect(Rect((WIDTH*7//8, HEIGHT//2 - 25), (50, 100)), 'black')
    screen.draw.filled_rect(Rect((WIDTH*7//8+10, HEIGHT//2 - 25), (10, 100)), 'white')
    screen.draw.filled_rect(Rect((WIDTH*7//8+30, HEIGHT//2 - 25), (10, 100)), 'white')
    
    game.dino.draw()

    screen.draw.text(f'Time: {game.clock}', color='yellow', topright=(WIDTH*15//16, HEIGHT//16), fontsize=32)

    if game.target:
        screen.draw.text(game.target, color='yellow', center=(WIDTH//2, HEIGHT*3//4), fontsize=48)

    if game.source:
        screen.draw.text(game.source, color='red', center=(WIDTH//2, HEIGHT*7//8), fontsize=48)

def update():
    game.frame_number = (game.frame_number + 1) % 60
    game.dino.update(game.frame_number)

# Keyboard Handling

def on_key_down(key):
    if not game.target:
        return

    source = game.source + str(key)[-1].lower()

    if source != game.target[:len(source)]:
        game.dino.kick()
        return

    game.source = source

    if game.source == game.target:
        if game.dino.pos[0] >= WIDTH*7//8:
            game.dino.pos = (WIDTH//2, HEIGHT//2)
            clock.schedule(celebrate, 1.0)
        else:
            game.dino.move(5, 0)
            clock.schedule(next_word, 0.5)

def on_key_up(key):
    game.dino.idle()

# Timers

def celebrate():
    game.target = 'VICTORY!'
    game.dino.move(random.randint(-1, 1), random.randint(-1, 1))
    clock.schedule(celebrate, 1.0)

def update_clock():
    game.clock += 1
    clock.schedule(update_clock, 1.0)

def next_word():
    while (target := random.choice(WORDS)) == game.target:
        pass

    game.target = target
    game.source = ''

    subprocess.Popen(['espeak', game.target], close_fds=True)

# Initialization

pygame.mouse.set_visible(False)         # Turn off mouse cursor
os.environ['SDL_VIDEO_CENTERED'] = '1'  # Center game window

game = Game()
clock.schedule(update_clock, 1.0)
clock.schedule(next_word, 1.0)
