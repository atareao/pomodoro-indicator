#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# pomodoro-indicator.py
#
# This file is part of Pomodoro-Indicator
#
# Copyright (C) 2014
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
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
gi.require_version('Gst', '1.0')
from gi.repository import Gst
from gi.repository import GLib
from gi.repository import GdkPixbuf
from gi.repository import AppIndicator3 as appindicator
from gi.repository import Notify
from gi.repository import GObject

import os
import json
import webbrowser
import dbus
from threading import Thread

from configurator import Configuration
from preferences_dialog import PreferencesDialog
from comun import _
import comun
from dbus.mainloop.glib import DBusGMainLoop

BUS_NAME = 'es.atareao.pomodoro'
BUS_PATH = '/es/atareao/pomodoro'

def add2menu(menu, text = None, icon = None, conector_event = None, conector_action = None):
	if text != None:
		menu_item = Gtk.ImageMenuItem.new_with_label(text)
		if icon:
			image = Gtk.Image.new_from_file(icon)
			menu_item.set_image(image)
			menu_item.set_always_show_image(True)
	else:
		if icon == None:
			menu_item = Gtk.SeparatorMenuItem()
		else:
			menu_item = Gtk.ImageMenuItem.new_from_file(icon)
			menu_item.set_always_show_image(True)
	if conector_event != None and conector_action != None:				
		menu_item.connect(conector_event,conector_action)
	menu_item.show()
	menu.append(menu_item)
	return menu_item

class Pomodoro_Indicator(GObject.GObject):
	__gsignals__ = {
		'session_end' : (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE,()),
		'break_end' : (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE,()),
	}
	def __init__(self):
		GObject.GObject.__init__(self)
		self.player = Gst.ElementFactory.make("playbin", "player")
		self.player.connect("about-to-finish",  self.on_player_finished)
		bus = self.player.get_bus()	
		bus.connect("message", self.on_player_message)		
		self.icon = comun.ICON
		self.active_icon = None
		self.about_dialog = None
		self.active = False
		self.animate = False
		self.frame = 0
		self.pomodoros = 0
		self.notification = Notify.Notification.new('','', None)
		self.read_preferences()
		#
		self.indicator = appindicator.Indicator.new ('Pomodoro-Indicator',\
			self.active_icon, appindicator.IndicatorCategory.HARDWARE)
		self.indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
		
		self.indicator.connect('scroll-event', self.on_scroll)
		
		menu = self.get_menu()
		self.indicator.set_menu(menu)
		self.connect('session_end', self.on_session_end)
		self.connect('break_end',self.on_break_end)

	def on_break_end(self,widget):
		self.frame = 0
		self.notification.update('Pomodoro-Indicator',
					_('Break ends'), os.path.join(comun.ICONDIR,'pomodoro-indicator-%s.svg'%(self.theme)))
		self.notification.show()					
		if self.play_sounds:
			self.play(self.break_sound_file)
		self.indicator.set_icon(os.path.join(comun.ICONDIR,'pomodoro-start-%s.svg'%(self.theme)))
		self.pomodoros+=1
		if self.pomodoros < self.max_pomodoros:			
			self.notification.update('Pomodoro-Indicator',
						_('Session starts'), os.path.join(comun.ICONDIR,'pomodoro-start-%s.svg'%(self.theme)))
			self.notification.show()			
			interval = int(self.session_length*60/36*1000)
			GLib.timeout_add(interval, self.countdown_session)
		else:
			self.pomodoros = 0
			self.animate = False
			self.active = False
			self.pomodoro_start.set_sensitive(True)
			self.pomodoro_stop.set_sensitive(False)
			
			
	def on_session_end(self,widget):
		self.active = True
		self.countdown_break()
		self.frame = 0
		if self.pomodoros == self.max_pomodoros - 1:
			interval = int(self.long_break_length*60/36*1000)
			self.notification.update('Pomodoro-Indicator',
						_('Session ends - long break starts'), os.path.join(comun.ICONDIR,'pomodoro-indicator-%s.svg'%(self.theme)))
		else:
			interval = int(self.break_length*60/36*1000)
			self.notification.update('Pomodoro-Indicator',
						_('Session ends - break starts'), os.path.join(comun.ICONDIR,'pomodoro-indicator-%s.svg'%(self.theme)))
		self.notification.show()
		if self.play_sounds:
			self.play(self.session_sound_file)
		self.indicator.set_icon(os.path.join(comun.ICONDIR,'pomodoro-indicator-%s.svg'%(self.theme)))
		GLib.timeout_add(interval, self.countdown_break)				
	
	def on_scroll(self, widget,steps,direcction):
		if self.active:
			self.on_pomodoro_stop(None)
		else:
			self.on_pomodoro_start(None)	
	
	def play(self,afile):	
		self.player.set_property('uri', 'file://'+afile)	
		self.player.set_state(Gst.State.PLAYING)  

	def on_player_finished(self, player):
		self.player = None
		self.player = Gst.ElementFactory.make("playbin", "player")
		self.player.connect("about-to-finish",  self.on_player_finished)
		bus = self.player.get_bus()	
		bus.connect("message", self.on_player_message)				
		
	def on_player_message(self, bus, message):
		t = message.type
		if t == Gst.Message.EOS:
			self.player.set_state(Gst.State.NULL)
		elif t == Gst.Message.ERROR:
			self.player.set_state(Gst.State.NULL)
			err, debug = message.parse_error()
			print("Error: %s" % err, debug)

	################## main functions ####################

	def read_preferences(self):
		configuration = Configuration()
		self.first_time = configuration.get('first-time')
		self.version = configuration.get('version')
		self.theme = configuration.get('theme')
		self.max_pomodoros = configuration.get('number_of_pomodoros')
		self.session_length = configuration.get('session_length')
		self.break_length = configuration.get('break_length')
		self.long_break_length = configuration.get('long_break_length')
		self.play_sounds = configuration.get('play_sounds')
		self.session_sound_file = configuration.get('session_sound_file')
		self.break_sound_file = configuration.get('break_sound_file')
		self.active_icon = comun.STATUS_ICON[configuration.get('theme')][0]
	

	################### menu creation ######################

	def get_help_menu(self):
		help_menu =Gtk.Menu()
		#
		add2menu(help_menu,text = _('Homepage...'),conector_event = 'activate',conector_action = lambda x: webbrowser.open('https://launchpad.net/pomodoro-indicator'))
		add2menu(help_menu,text = _('Get help online...'),conector_event = 'activate',conector_action = lambda x: webbrowser.open('https://answers.launchpad.net/pomodoro-indicator'))
		add2menu(help_menu,text = _('Translate this application...'),conector_event = 'activate',conector_action = lambda x: webbrowser.open('https://translations.launchpad.net/pomodoro-indicator'))
		add2menu(help_menu,text = _('Report a bug...'),conector_event = 'activate',conector_action = lambda x: webbrowser.open('https://bugs.launchpad.net/pomodoro-indicator'))
		add2menu(help_menu)
		web = add2menu(help_menu,text = _('Homepage'),conector_event = 'activate',conector_action = lambda x: webbrowser.open('http://www.atareao.es/tag/pomodoro-indicator'))
		twitter = add2menu(help_menu,text = _('Follow us in Twitter'),conector_event = 'activate',conector_action = lambda x: webbrowser.open('https://twitter.com/atareao'))
		googleplus = add2menu(help_menu,text = _('Follow us in Google+'),conector_event = 'activate',conector_action = lambda x: webbrowser.open('https://plus.google.com/118214486317320563625/posts'))
		facebook = add2menu(help_menu,text = _('Follow us in Facebook'),conector_event = 'activate',conector_action = lambda x: webbrowser.open('http://www.facebook.com/elatareao'))
		add2menu(help_menu)
		#		
		web.set_image(Gtk.Image.new_from_file(os.path.join(comun.SOCIALDIR,'web.svg')))
		web.set_always_show_image(True)
		twitter.set_image(Gtk.Image.new_from_file(os.path.join(comun.SOCIALDIR,'twitter.svg')))
		twitter.set_always_show_image(True)
		googleplus.set_image(Gtk.Image.new_from_file(os.path.join(comun.SOCIALDIR,'googleplus.svg')))
		googleplus.set_always_show_image(True)
		facebook.set_image(Gtk.Image.new_from_file(os.path.join(comun.SOCIALDIR,'facebook.svg')))
		facebook.set_always_show_image(True)
		
		add2menu(help_menu)
		add2menu(help_menu,text = _('About'),conector_event = 'activate',conector_action = self.on_about_item)
		#
		help_menu.show()
		return(help_menu)

	def get_menu(self):
		"""Create and populate the menu."""
		menu = Gtk.Menu()
			
		self.pomodoro_start = Gtk.MenuItem.new_with_label(_('Start'))
		self.pomodoro_start.connect('activate',self.on_pomodoro_start)
		self.pomodoro_start.show()
		menu.append(self.pomodoro_start)

		self.pomodoro_stop = Gtk.MenuItem.new_with_label(_('Stop'))
		self.pomodoro_stop.connect('activate',self.on_pomodoro_stop)
		self.pomodoro_stop.show()
		self.pomodoro_stop.set_sensitive(False)
		menu.append(self.pomodoro_stop)		
		
		separator1 = Gtk.SeparatorMenuItem()
		separator1.show()
		menu.append(separator1)
		#
		menu_preferences = Gtk.MenuItem.new_with_label(_('Preferences'))		
		menu_preferences.connect('activate',self.on_preferences_item)
		menu_preferences.show()
		menu.append(menu_preferences)
		
		menu_help = Gtk.MenuItem.new_with_label(_('Help'))		
		menu_help.set_submenu(self.get_help_menu())
		menu_help.show()
		menu.append(menu_help)
		#
		separator2 = Gtk.SeparatorMenuItem()
		separator2.show()
		menu.append(separator2)
		#
		menu_exit = Gtk.MenuItem.new_with_label(_('Exit'))
		menu_exit.connect('activate',self.on_quit_item)
		menu_exit.show()
		menu.append(menu_exit)
		#
		menu.show()
		return(menu)
	
	def on_pomodoro_start(self,widget):
		self.active = True
		self.pomodoro_start.set_sensitive(False)
		self.pomodoro_stop.set_sensitive(True)	
		self.notification.update('Pomodoro-Indicator',
					_('Session starts'), os.path.join(comun.ICONDIR,'pomodoro-start-%s.svg'%(self.theme)))
		self.notification.show()
		self.countdown_session()
		interval = int(self.session_length*60/36*1000)
		print(interval)
		GLib.timeout_add(interval, self.countdown_session)

	def on_pomodoro_stop(self,widget):
		self.active = False
		self.pomodoros = 0
		self.pomodoro_start.set_sensitive(True)
		self.pomodoro_stop.set_sensitive(False)
		self.indicator.set_icon(os.path.join(comun.ICONDIR,'pomodoro-start-%s.svg'%(self.theme)))
		self.notification.update('Pomodoro-Indicator',
					_('Session stop'), os.path.join(comun.ICONDIR,'pomodoro-stop-%s.svg'%(self.theme)))
		self.notification.show()

	def countdown_session(self):
		if not self.active:
			self.animate = False
			self.indicator.set_icon(self.active_icon)
			self.frame = 0
			return False
		else:
			self.animate = True
			afile = os.path.join(comun.ICONDIR,'pomodoro-indicator-%s-%02d.svg'%(self.theme,self.frame))
			self.indicator.set_icon(afile)
			self.frame += 1
			if self.frame == 36:
				self.emit('session_end')
				return False
			return True
			
	def countdown_break(self):
		if not self.active:
			self.animate = False
			self.indicator.set_icon(self.active_icon)
			self.frame = 0
			return False
		else:
			self.animate = True
			afile = os.path.join(comun.ICONDIR,'pomodoro-indicator-%s-%02d.svg'%(self.theme,self.frame))
			self.indicator.set_icon(afile)
			self.frame += 1
			if self.frame == 36:
				self.emit('break_end')
				return False
			return True
		
	def get_about_dialog(self):
		"""Create and populate the about dialog."""
		about_dialog = Gtk.AboutDialog()
		about_dialog.set_name(comun.APPNAME)
		about_dialog.set_version(comun.VERSION)
		about_dialog.set_copyright('Copyrignt (c) 2014-2016\nLorenzo Carbonell Cerezo')
		about_dialog.set_comments(_('An indicator for Pomodoro Technique'))
		about_dialog.set_license(''+
		'This program is free software: you can redistribute it and/or modify it\n'+
		'under the terms of the GNU General Public License as published by the\n'+
		'Free Software Foundation, either version 3 of the License, or (at your option)\n'+
		'any later version.\n\n'+
		'This program is distributed in the hope that it will be useful, but\n'+
		'WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY\n'+
		'or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for\n'+
		'more details.\n\n'+
		'You should have received a copy of the GNU General Public License along with\n'+
		'this program.  If not, see <http://www.gnu.org/licenses/>.')
		about_dialog.set_website('http://www.atareao.es')
		about_dialog.set_website_label('http://www.atareao.es')
		about_dialog.set_authors(['Lorenzo Carbonell <https://launchpad.net/~lorenzo-carbonell>'])
		about_dialog.set_documenters(['Lorenzo Carbonell <https://launchpad.net/~lorenzo-carbonell>'])
		about_dialog.set_translator_credits(''+
		'Lorenzo Carbonell <https://launchpad.net/~lorenzo-carbonell>\n')
		about_dialog.set_icon(GdkPixbuf.Pixbuf.new_from_file(comun.ICON))
		about_dialog.set_logo(GdkPixbuf.Pixbuf.new_from_file(comun.ICON))
		about_dialog.set_program_name(comun.APPNAME)
		return about_dialog

	###################### callbacks for the menu #######################
	def on_preferences_item(self, widget, data=None):
		widget.set_sensitive(False)
		preferences_dialog = PreferencesDialog()
		if 	preferences_dialog.run() == Gtk.ResponseType.ACCEPT:
			preferences_dialog.close_ok()
			self.read_preferences()
		preferences_dialog.hide()
		preferences_dialog.destroy()
		self.indicator.set_icon(self.active_icon)
		widget.set_sensitive(True)

	def on_quit_item(self, widget, data=None):
		exit(0)

	def on_about_item(self, widget, data=None):
		if self.about_dialog:
			self.about_dialog.present()
		else:
			self.about_dialog = self.get_about_dialog()
			self.about_dialog.run()
			self.about_dialog.destroy()
			self.about_dialog = None

#################################################################

def main():

	if dbus.SessionBus().request_name('es.atareao.PomodoroIndicator') != dbus.bus.REQUEST_NAME_REPLY_PRIMARY_OWNER:
		print("application already running")
		exit(0)		
	GObject.threads_init()
	Gst.init(None)
	Gst.init_check(None)
	Notify.init('pomodoro-indicator')
	pomodoro_indicator=Pomodoro_Indicator()
	Gtk.main()

if __name__ == "__main__":
	main()
