#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# player.py
#
# This file is part of Pomodoro-Indicator
#
# Copyright (C) 2014 - 2017
# Lorenzo Carbonell Cerezo <lorenzo.carbonell.cerezo@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import gi
try:
    gi.require_version('Gst', '1.0')
    gi.require_version('Gtk', '3.0')
    gi.require_version('GLib', '2.0')
    gi.require_version('GObject', '2.0')
except Exception as e:
    print(e)
    exit(-1)
from gi.repository import Gst
from gi.repository import GLib
from gi.repository import GObject
from enum import Enum


class Status(Enum):
    STOPPED = 0
    PLAYING = 1
    PAUSED = 2


class Player(GObject.GObject):
    __gsignals__ = {
        'started': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (int,)),
        'stopped': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (int,)),
        'paused': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (int,)),
    }

    def __init__(self):
        GObject.GObject.__init__(self)
        Gst.init_check(None)
        self.status = Status.STOPPED
        self.player = None
        self.speed = 1.0
        self.volume = 1.0
        self.removesilence = False
        self.equalizer = {'band0': 0, 'band1': 0, 'band2': 0, 'band3': 0,
                          'band4': 0, 'band5': 0, 'band6': 0, 'band7': 0,
                          'band8': 0, 'band9': 0}
        self.lastpos = 0

    def get_status(self):
        '''
        Get the status of the player
        '''
        if self.player is not None:
            if self.player.get_state(Gst.CLOCK_TIME_NONE)[1] ==\
                    Gst.State.PLAYING:
                return Status.PLAYING
            elif self.player.get_state(Gst.CLOCK_TIME_NONE)[1] ==\
                    Gst.State.PAUSED:
                return Status.PAUSED
        return Status.STOPPED

    def get_player(self):
        player = Gst.parse_launch('uridecodebin name=urisrc !\
 audioconvert ! audioresample ! queue ! removesilence name=removesilence !\
 audioconvert ! audioresample ! queue ! scaletempo !\
 audioconvert ! audioresample ! volume name=volume !\
 equalizer-10bands name=equalizer ! autoaudiosink')
        bus = player.get_bus()
        bus.add_signal_watch()
        bus.connect('message::state-changed', self.on_state_changed)
        bus.connect('message', self.on_player_message)
        return player

    def emit(self, *args):
        GLib.idle_add(GObject.GObject.emit, self, *args)

    def on_player_message(self, bus, message):
        t = message.type
        # print('---', t, '---')
        if t == Gst.MessageType.EOS:
            self.player.set_state(Gst.State.NULL)
        elif t == Gst.MessageType.ERROR:
            self.player.set_state(Gst.State.NULL)
            err, debug = message.parse_error()
            print('Error: %s' % err, debug)

    def on_state_changed(self, bus, msg):
        old, new, pending = msg.parse_state_changed()
        # print('---', old, new, pending, '---')

    def set_filename(self, filename):
        if self.player is not None:
            self.player.set_state(Gst.State.NULL)
        self.player = self.get_player()
        self.player.get_by_name('urisrc').set_property('uri',
                                                       'file://' + filename)

    def play(self):
        '''
        Play the player
        '''
        if self.player is not None:
            self.player.set_state(Gst.State.PLAYING)
            self.player.get_state(Gst.CLOCK_TIME_NONE)
            self.player.get_by_name('removesilence').set_property(
                'remove', self.removesilence)
            self.player.get_by_name('volume').set_property('volume',
                                                           self.volume)
            self.player.get_by_name('equalizer').set_property(
                'band0', self.equalizer['band0'])
            self.player.get_by_name('equalizer').set_property(
                'band1', self.equalizer['band1'])
            self.player.get_by_name('equalizer').set_property(
                'band2', self.equalizer['band2'])
            self.player.get_by_name('equalizer').set_property(
                'band3', self.equalizer['band3'])
            self.player.get_by_name('equalizer').set_property(
                'band4', self.equalizer['band4'])
            self.player.get_by_name('equalizer').set_property(
                'band5', self.equalizer['band5'])
            self.player.get_by_name('equalizer').set_property(
                'band6', self.equalizer['band6'])
            self.player.get_by_name('equalizer').set_property(
                'band7', self.equalizer['band7'])
            self.player.get_by_name('equalizer').set_property(
                'band8', self.equalizer['band8'])
            self.player.get_by_name('equalizer').set_property(
                'band9', self.equalizer['band9'])
            pos = self.player.query_position(Gst.Format.TIME)[1]
            self.player.seek(self.speed, Gst.Format.TIME, Gst.SeekFlags.FLUSH,
                             Gst.SeekType.SET, pos, Gst.SeekType.NONE, -1)
            self.status = Status.PLAYING
            self.emit('started', self.get_position())

    def pause(self):
        '''
        Pause the player
        '''
        if self.player is not None:
            self.player.set_state(Gst.State.PAUSED)
            self.status = Status.PAUSED
            self.emit('paused', self.get_position())

    def stop(self):
        '''
        Stop the player
        '''
        if self.player is not None:
            self.player.set_state(Gst.State.READY)
            self.status = Status.STOPPED
            self.emit('stopped', self.get_position())

    def set_volume(self, volume):
        '''
        Set player volume
        '''
        self.volume = volume
        if self.get_status() == Status.PLAYING:
            self.play()

    def get_volume(self):
        '''
        Get player volume
        '''
        return self.volume

    def set_remove_silence(self, removesilence):
        '''
        Set if player removes silences
        '''
        self.removesilence = removesilence
        if self.get_status() == Status.PLAYING:
            self.play()

    def get_removesilence(self):
        '''
        Get if player removes silences
        '''
        return self.removesilence

    def set_equalizaer(self, equalizer):
        self.equalizer = equalizer
        if self.get_status() == Status.PLAYING:
            self.play()

    def set_equalizer_by_band(self, band, gain):
        '''
        Set player equalizer

        band0 gain for the frequency band 29 Hz, from -24 dB to +12 dB
        band1 gain for the frequency band 59 Hz, from -24 dB to +12 dB
        band2 gain for the frequency band 119 Hz, from -24 dB to +12 dB
        band3 gain for the frequency band 237 Hz, from -24 dB to +12 dB
        band4 gain for the frequency band 474 Hz, from -24 dB to +12 dB
        band5 gain for the frequency band 947 Hz, from -24 dB to +12 dB
        band6 gain for the frequency band 1889 Hz, from -24 dB to +12 dB
        band7 gain for the frequency band 3770 Hz, from -24 dB to +12 dB
        band8 gain for the frequency band 7523 Hz, from -24 dB to +12 dB
        band9 gain for the frequency band 15011 Hz, from -24 dB to +12 dB
        '''
        if band >= 0 and band <= 9 and gain >= -24 and gain <= 12:
            band = 'band{0}'.format(band)
            self.equalizer[band] = gain
        if self.get_status() == Status.PLAYING:
            self.play()

    def get_equalizer(self):
        '''
        Get player equalizer
        '''
        return self.equalizer

    def set_speed(self, speed):
        '''
        Set player speed
        '''
        self.speed = speed
        if self.get_status() == Status.PLAYING:
            self.play()

    def get_speed(self):
        '''
        Get player speed
        '''
        return self.speed

    def set_position(self, position):
        if self.player is not None:
            self.player.get_state(Gst.CLOCK_TIME_NONE)
            self.player.set_state(Gst.State.PAUSED)
            try:
                assert self.player.seek_simple(Gst.Format.TIME,
                                               Gst.SeekFlags.FLUSH,
                                               position * Gst.SECOND)
                self.player.get_state(Gst.CLOCK_TIME_NONE)
                pos = self.player.query_position(Gst.Format.TIME)[1]
                self.player.seek(self.speed, Gst.Format.TIME,
                                 Gst.SeekFlags.FLUSH, Gst.SeekType.SET, pos,
                                 Gst.SeekType.NONE, -1)
            except AssertionError as e:
                print(e)
            self.player.set_state(Gst.State.PLAYING)

    def get_position(self):
        if self.player is not None:
            self.player.get_state(Gst.CLOCK_TIME_NONE)
            nanosecs = self.player.query_position(Gst.Format.TIME)[1]
            position = float(nanosecs) / Gst.SECOND
            return position
        return 0

    def get_duration(self):
        if self.player is not None:
            self.player.get_state(Gst.CLOCK_TIME_NONE)
            duration_nanosecs = self.player.query_duration(Gst.Format.TIME)[1]
            duration = float(duration_nanosecs) / Gst.SECOND
            return duration
        return 0


if __name__ == '__main__':
    import time

    def fin(player, position, what):
        print(player, position, what)

    print('start')
    player = Player()
    # player.set_filename('/datos/Descargas/test.ogg')
    player.set_filename('/home/lorenzo/Descargas/sample.mp3')
    player.set_speed(1.5)
    player.set_equalizer(1, -12)
    player.set_equalizer(3, -12)
    player.set_equalizer(5, -12)
    player.set_equalizer(7, -12)
    print(player.get_status())
    player.play()
    time.sleep(5)
    print(player.get_status())
    # player.set_volume(1)
    # player.set_speed(2.0)
    # player.set_remove_silence(True)
    player.set_equalizer(1, 12)
    player.set_equalizer(3, 12)
    player.set_equalizer(5, 12)
    player.set_equalizer(7, 12)
    player.set_speed(2.0)
    time.sleep(5)
    player.pause()
    print(player.get_status())
    time.sleep(1)
    print(player.get_position())
    '''
    player.set_filename('/home/lorenzo/Descargas/sample.mp3')
    player.connect('started', fin, 'started')
    player.connect('paused', fin, 'paused')
    player.connect('stopped', fin, 'stopped')
    player.play()
    player.set_speed(2)
    time.sleep(10)
    player.set_position(10)
    time.sleep(2)
    player.set_position(50)
    time.sleep(2)
    '''
