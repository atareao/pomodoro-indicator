#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# preferences_dialog.py
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
    gi.require_version('Gtk', '3.0')
except Exception as e:
    print(e)
    exit(1)
from gi.repository import Gtk
import os
import shutil
import glob
from . import comun
from .comun import _
from .configurator import Configuration


def create_or_remove_autostart(create):
    if not os.path.exists(comun.AUTOSTART_DIR):
        os.makedirs(comun.AUTOSTART_DIR)
    if create:
        if not os.path.exists(comun.FILE_AUTO_START):
            shutil.copyfile(comun.FILE_AUTO_START_ORIG, comun.FILE_AUTO_START)
    else:
        if os.path.exists(comun.FILE_AUTO_START):
            os.remove(comun.FILE_AUTO_START)


def get_sounds():
    sounds = []
    personal_dir = os.path.expanduser('~/.config/pomodoro-indicator/sounds')
    if os.path.exists(personal_dir):
        for filename in glob.glob(os.path.join(personal_dir, '*.ogg')):
            sounds.append([os.path.basename(filename), filename])
    if os.path.exists(comun.SOUNDIR):
        for filename in glob.glob(os.path.join(comun.SOUNDIR, '*.ogg')):
            sounds.append([os.path.basename(filename), filename])
    return sounds


def get_selected_value_in_combo(combo):
    model = combo.get_model()
    return model.get_value(combo.get_active_iter(), 1)


def select_value_in_combo(combo, value):
    model = combo.get_model()
    for i, item in enumerate(model):
        if value == item[1]:
            combo.set_active(i)
            return
    combo.set_active(0)


class PreferencesDialog(Gtk.Dialog):
    def __init__(self):
        Gtk.Dialog.__init__(self, 'Pomodoro Indicator | ' + _('Preferences'),
                            None,
                            Gtk.DialogFlags.MODAL |
                            Gtk.DialogFlags.DESTROY_WITH_PARENT,
                            (Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,
                                Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT))
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        # self.set_size_request(400, 230)
        self.connect('close', self.close_application)
        self.set_icon_from_file(comun.ICON)
        #
        vbox0 = Gtk.VBox(spacing=5)
        vbox0.set_border_width(5)
        self.get_content_area().add(vbox0)
        #
        notebook = Gtk.Notebook.new()
        vbox0.add(notebook)
        #
        vbox1 = Gtk.VBox(spacing=5)
        vbox1.set_border_width(5)
        notebook.append_page(vbox1, Gtk.Label.new(_('Main')))
        frame1 = Gtk.Frame()
        vbox1.pack_start(frame1, False, True, 1)
        table1 = Gtk.Table(8, 2, False)
        frame1.add(table1)
        #
        label0 = Gtk.Label(_('Number of pomodoros') + ':')
        label0.set_alignment(0, 0.5)
        table1.attach(label0, 0, 1, 0, 1, xpadding=5, ypadding=5)
        self.spinbutton0 = Gtk.SpinButton()
        self.spinbutton0.set_adjustment(Gtk.Adjustment(2, 1, 20, 1, 10, 0))
        table1.attach(self.spinbutton0, 1, 2, 0, 1, xpadding=5, ypadding=5)
        #
        label1 = Gtk.Label(_('Set session length (minutes)') + ':')
        label1.set_alignment(0, 0.5)
        table1.attach(label1, 0, 1, 1, 2, xpadding=5, ypadding=5)
        self.spinbutton1 = Gtk.SpinButton()
        self.spinbutton1.set_adjustment(Gtk.Adjustment(25, 1, 1440, 1, 10, 0))
        table1.attach(self.spinbutton1, 1, 2, 1, 2, xpadding=5, ypadding=5)

        label2 = Gtk.Label(_('Set break length (minutes)') + ':')
        label2.set_alignment(0, 0.5)
        table1.attach(label2, 0, 1, 2, 3, xpadding=5, ypadding=5)
        self.spinbutton2 = Gtk.SpinButton()
        self.spinbutton2.set_adjustment(Gtk.Adjustment(25, 1, 1440, 1, 10, 0))
        table1.attach(self.spinbutton2, 1, 2, 2, 3, xpadding=5, ypadding=5)

        label_long_break = Gtk.Label(_(
            'Set long break length (minutes)') + ':')
        label_long_break.set_alignment(0, 0.5)
        table1.attach(label_long_break, 0, 1, 3, 4, xpadding=5, ypadding=5)
        self.spinbutton3 = Gtk.SpinButton()
        self.spinbutton3.set_adjustment(Gtk.Adjustment(25, 1, 1440, 1, 10, 0))
        table1.attach(self.spinbutton3, 1, 2, 3, 4, xpadding=5, ypadding=5)

        label4 = Gtk.Label(_('Play sounds') + ':')
        label4.set_alignment(0, 0.5)
        table1.attach(label4, 0, 1, 4, 5, xpadding=5, ypadding=5)
        self.switch4 = Gtk.Switch()
        table1.attach(self.switch4, 1, 2, 4, 5, xpadding=5, ypadding=5,
                      xoptions=Gtk.AttachOptions.SHRINK)
        sounds = Gtk.ListStore(str, str)
        for sound in get_sounds():
            sounds.append(sound)
        label5 = Gtk.Label(_('Sound on session end') + ':')
        label5.set_alignment(0, 0.5)
        table1.attach(label5, 0, 1, 5, 6, xpadding=5, ypadding=5)
        self.comboboxsound5 = Gtk.ComboBox.new()
        self.comboboxsound5.set_model(sounds)
        cell1 = Gtk.CellRendererText()
        self.comboboxsound5.pack_start(cell1, True)
        self.comboboxsound5.add_attribute(cell1, 'text', 0)
        table1.attach(self.comboboxsound5, 1, 2, 5, 6,
                      xoptions=Gtk.AttachOptions.FILL,
                      yoptions=Gtk.AttachOptions.FILL,
                      xpadding=5,
                      ypadding=5)
        label6 = Gtk.Label(_('Sound on break end') + ':')
        label6.set_alignment(0, 0.5)
        table1.attach(label6, 0, 1, 6, 7, xpadding=5, ypadding=5)
        self.comboboxsound6 = Gtk.ComboBox.new()
        self.comboboxsound6.set_model(sounds)
        cell1 = Gtk.CellRendererText()
        self.comboboxsound6.pack_start(cell1, True)
        self.comboboxsound6.add_attribute(cell1, 'text', 0)
        table1.attach(self.comboboxsound6, 1, 2, 6, 7,
                      xoptions=Gtk.AttachOptions.FILL,
                      yoptions=Gtk.AttachOptions.FILL,
                      xpadding=5,
                      ypadding=5)
        label7 = Gtk.Label(_('Autostart') + ':')
        label7.set_alignment(0, 0.5)
        table1.attach(label7, 0, 1, 7, 8, xpadding=5, ypadding=5)
        self.switch7 = Gtk.Switch()
        table1.attach(self.switch7, 1, 2, 7, 8, xpadding=5, ypadding=5,
                      xoptions=Gtk.AttachOptions.SHRINK)
        label8 = Gtk.Label(_('Icon light') + ':')
        label8.set_alignment(0, 0.5)
        table1.attach(label8, 0, 1, 8, 9, xpadding=5, ypadding=5)
        self.switch8 = Gtk.Switch()
        table1.attach(self.switch8, 1, 2, 8, 9, xpadding=5, ypadding=5,
                      xoptions=Gtk.AttachOptions.SHRINK)
        #
        self.load_preferences()
        #
        self.show_all()

    def close_application(self, widget, event):
        self.hide()

    def messagedialog(self, title, message):
        dialog = Gtk.MessageDialog(None,
                                   Gtk.DialogFlags.MODAL,
                                   Gtk.MessageType.INFO,
                                   buttons=Gtk.ButtonsType.OK)
        dialog.set_markup("<b>%s</b>" % title)
        dialog.format_secondary_markup(message)
        dialog.run()
        dialog.destroy()

    def close_ok(self):
        self.save_preferences()

    def load_preferences(self):
        configuration = Configuration()
        first_time = configuration.get('first-time')
        version = configuration.get('version')
        if first_time or version != comun.VERSION:
            configuration.set_defaults()
            configuration.read()
        self.spinbutton0.set_value(configuration.get('number_of_pomodoros'))
        self.spinbutton1.set_value(configuration.get('session_length'))
        self.spinbutton2.set_value(configuration.get('break_length'))
        self.spinbutton3.set_value(configuration.get('long_break_length'))
        self.switch4.set_active(configuration.get('play_sounds'))
        select_value_in_combo(self.comboboxsound5,
                              configuration.get('session_sound_file'))
        select_value_in_combo(self.comboboxsound6,
                              configuration.get('break_sound_file'))
        self.switch7.set_active(os.path.exists(comun.FILE_AUTO_START))
        self.switch8.set_active(configuration.get('theme') == 'light')

    def save_preferences(self):
        configuration = Configuration()
        configuration.set('first-time', False)
        configuration.set('version', comun.VERSION)
        configuration.set('number_of_pomodoros', self.spinbutton0.get_value())
        configuration.set('session_length', self.spinbutton1.get_value())
        configuration.set('break_length', self.spinbutton2.get_value())
        configuration.set('long_break_length', self.spinbutton3.get_value())
        configuration.set('play_sounds', self.switch4.get_active())
        configuration.set('session_sound_file',
                          get_selected_value_in_combo(self.comboboxsound5))
        configuration.set('break_sound_file',
                          get_selected_value_in_combo(self.comboboxsound6))
        create_or_remove_autostart(self.switch7.get_active())
        if self.switch8.get_active():
            configuration.set('theme', 'light')
        else:
            configuration.set('theme', 'dark')
        configuration.save()


if __name__ == "__main__":
    cm = PreferencesDialog()
    if cm.run() == Gtk.ResponseType.ACCEPT:
            print(1)
            cm.close_ok()
    cm.hide()
    cm.destroy()
    exit(0)
