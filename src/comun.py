#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# comun.py
#
# This file is part of PushBullet-Indicator
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

import urllib.request

__author__ = 'Lorenzo Carbonell <lorenzo.carbonell.cerezo@gmail.com>'
__copyright__ = 'Copyright (c) 2014 Lorenzo Carbonell'
__license__ = 'GPLV3'
__url__ = 'http://www.atareao.es'

import os
import locale
import gettext

######################################

def is_package():
	return not os.path.dirname(os.path.abspath(__file__)).endswith('src')

######################################

PARAMS = {
			'first-time':True,
			'version':'',
			'autostart':False,
			'theme':'light',
			'session_length':25,
			'break_length':5,
			'long_break_length':20,
			'number_of_pomodoros':4,
			'play_sounds':True,
			'session_sound_file':'default',
			'break_sound_file':'default'
			}


APP = 'pomodoro-indicator'
APPCONF = APP + '.conf'
APPDATA = APP + '.data'
APPNAME = 'Pomodoro-Indicator'
CONFIG_DIR = os.path.join(os.path.expanduser('~'),'.config')
CONFIG_APP_DIR = os.path.join(CONFIG_DIR, APP)
CONFIG_FILE = os.path.join(CONFIG_APP_DIR, APPCONF)
DATA_FILE = os.path.join(CONFIG_APP_DIR, APPDATA)
AUTOSTART_DIR = os.path.join(CONFIG_DIR,'autostart')
FILE_AUTO_START = os.path.join(AUTOSTART_DIR,'pomodoro-indicator-autostart.desktop')
if not os.path.exists(CONFIG_APP_DIR):
	os.makedirs(CONFIG_APP_DIR)

print(os.path.dirname(os.path.abspath(__file__)))

if is_package():
	ROOTDIR = '/opt/extras.ubuntu.com/pomodoro-indicator/share/'
	LANGDIR = os.path.join(ROOTDIR, 'locale-langpack')
	APPDIR = os.path.join(ROOTDIR, APP)
	ICONDIR = os.path.join(APPDIR, 'icons')
	SOCIALDIR = os.path.join(APPDIR, 'social')
	SOUNDIR = os.path.join(APPDIR, 'sounds')
	CHANGELOG = os.path.join(APPDIR,'changelog')
	FILE_AUTO_START_ORIG = os.path.join(APPDIR,'pomodoro-indicator-autostart.desktop')
else:
	ROOTDIR = os.path.dirname(__file__)
	LANGDIR = os.path.join(ROOTDIR, 'template1')
	APPDIR = os.path.join(ROOTDIR, APP)
	ICONDIR =  os.path.normpath(os.path.join(ROOTDIR, '../data/icons'))
	SOCIALDIR =  os.path.normpath(os.path.join(ROOTDIR, '../data/social'))
	SOUNDIR =  os.path.normpath(os.path.join(ROOTDIR, '../data/sounds'))
	DEBIANDIR = os.path.normpath(os.path.join(ROOTDIR, '../debian'))
	CHANGELOG = os.path.join(DEBIANDIR,'changelog')
	FILE_AUTO_START_ORIG = os.path.join(os.path.normpath(os.path.join(ROOTDIR, '../data')),'pomodoro-indicator-autostart.desktop')
ICON = os.path.join(ICONDIR,'pomodoro-indicator.svg')
DEFAULT_SESSION_SOUND_FILE = os.path.join(SOUNDIR,'ringbell.ogg')
DEFAULT_BREAK_SOUND_FILE = os.path.join(SOUNDIR,'gong.ogg')
STATUS_ICON = {}
STATUS_ICON['light'] = (os.path.join(ICONDIR,'pomodoro-start-light.svg'),os.path.join(ICONDIR,'pomodoro-stop-light.svg'))
STATUS_ICON['dark'] = (os.path.join(ICONDIR,'pomodoro-start-dark.svg'),os.path.join(ICONDIR,'pomodoro-stop-dark.svg'))



f = open(CHANGELOG,'r')
line = f.readline()
f.close()
pos=line.find('(')
posf=line.find(')',pos)
VERSION = line[pos+1:posf].strip()
if not is_package():
	VERSION = VERSION + '-src'
try:
	current_locale, encoding = locale.getdefaultlocale()
	language = gettext.translation(APP, LANGDIR, [current_locale])
	language.install()
	_ = language.gettext
except Exception as e:
	_ = str
	
def read_from_url(url):
	try:
		url = url.replace(' ','%20')
		request = urllib.request.Request(url, headers={'User-Agent' : 'Magic Browser'})
		f = urllib.request.urlopen(request)
		json_string = f.read()
		f.close()
		return json_string
	except:
		return None

def internet_on():
	try:
		response=urllib.request.urlopen('http://google.com',timeout=1)
		return True
	except:
		pass
	return False

	
