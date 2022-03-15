#from logging import root
from kivymd.app import MDApp
from kivy.core.window import Window
from kivy.clock import Clock
import json
import configparser
import requests                 # For getting data from server
import socket  
from ipaddress import ip_address
#from logging import root
from datetime import datetime
#from kivymd.uix.behaviors.toggle_behavior import MDToggleButton
#from kivymd.uix.button import MDRectangleFlatButton
from kivy.properties import ObjectProperty, NumericProperty,  StringProperty
import threading
#from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.list import OneLineListItem

current_screen = 'run'
IP_address = ''
run_button = ''

# Read settings from the config file
settings = configparser.ConfigParser()
settings.read('octoprint.cfg')
host = settings.get('APISettings', 'host')
nicname = settings.get('APISettings', 'nicname')
apikey = settings.get('APISettings', 'apikey')
debug = int(settings.get('Debug', 'debug_enabled'))

# Define Octoprint constants
httptimeout = 3   # http request timeout in seconds
printerapiurl = 'http://' + host + '/api/printer'
printheadurl = 'http://' + host + '/api/printer/printhead'
#bedurl = 'http://' + host + '/api/printer/bed'
#toolurl = 'http://' + host + '/api/printer/tool'
jobapiurl = 'http://' + host + '/api/job'
connectionurl = 'http://' + host + '/api/connection'
commandurl = 'http://' + host + '/api/printer/command'
filesapiurl = 'http://' + host + '/api/files'
headers = {'X-Api-Key': apikey, 'content-type': 'application/json'}


class MainApp(MDApp):
    local_IP = StringProperty('')
    curr_status = StringProperty ('')
    job_filename = StringProperty ('')
    curr_time = StringProperty ('')
       
    def run_routine(self):
        # SHow the RUN screen
        threading.Timer(2, self.run_routine).start()
        now = datetime.now()
        self.current_time = now.strftime("%H:%M")
        r = requests.get(jobapiurl, headers=headers, timeout=1)
        self.printerstate = r.json()['state']
        self.jobfilename = r.json()['job']['file']['name']
        jobpercent = r.json()['progress']['completion']
        jobprinttime = r.json()['progress']['printTime']
        jobprinttimeleft = r.json()['progress']['printTimeLeft']
        if self.jobfilename is not None:
            self.jobfilenamefull = self.jobfilename
            self.jobfilename = self.jobfilename[:25]  # Shorten filename to 25 characters
        else:
            self.jobfilename = '-'

        if self.printerstate is not None:
            self.printerstate = self.printerstate
        else:
            self.printerstate = 'Unknown'

        if jobpercent is not None:
            jobpercent = int(jobpercent)
            jobpercent = str(jobpercent) + '%'
            #progressbar.value = jobpercent
        else:
            jobpercent = '---%'
            #progressbar.value = 0

        if jobprinttime is not None:
            hours = int(jobprinttime / 60 / 60)
            if hours > 0:
                minutes = int(jobprinttime / 60) - (60 * hours)
            else:
                minutes = int(jobprinttime / 60)
            seconds = int(jobprinttime % 60)
            jobprinttime = str(hours).zfill(2) + ':' + \
                str(minutes).zfill(2) + ':' + str(seconds).zfill(2)
        else:
            jobprinttime = '00:00:00'

        if jobprinttimeleft is not None:
            hours = int(jobprinttimeleft / 60 / 60)
            if hours > 0:
                minutes = int(jobprinttimeleft / 60) - (60 * hours)
            else:
                minutes = int(jobprinttimeleft / 60)
            seconds = int(jobprinttimeleft % 60)
            jobprinttimeleft = str(hours).zfill(2) + \
                ':' + str(minutes).zfill(2) + ':' + str(seconds).zfill(2)
        else:
            jobprinttimeleft = '00:00:00'

            self.local_IP = self.IP_address
            print ('current_time = ' + self.current_time)
            self.curr_time = self.current_time
            print ('jobfilename = ' + self.jobfilename)
            self.job_filename = self.jobfilename
            print ('jobpercent = ' + jobpercent)
            #self.ids.jobpercent.text = jobpercent
            print ('jobprinttime = ' + jobprinttime)
            #self.ids.jobprinttime.text = jobfilename
            print ('jobprinttimeleft = ' + jobprinttimeleft)
    #        self.jobfilename = jobfilename
            print ('printerstate = ' + self.printerstate)
            self.curr_status = self.printerstate       

    def run_mode(self):
        if self.root.ids.run_icon.icon == 'run':
            self.root.ids.run_icon.icon = 'pause'
            self.root.ids.cancel_icon.disabled = False 
            command_data = {'command': 'start'}
        else:
            self.root.ids.run_icon.icon = 'run'
            self.root.ids.cancel_icon.disabled = False 
            command_data = {'command': 'pause'}
        r = requests.post(jobapiurl, headers=headers, json=command_data, timeout=httptimeout)
        print('STATUS CODE: ' + str(r.status_code))   
        
    def cancel_mode(self):
        self.root.ids.cancel_icon.disabled = True 
        self.root.ids.run_icon.icon = 'run'
        command_data = {'command': 'cancel'}
        r = requests.post(jobapiurl, headers=headers, json=command_data, timeout=httptimeout)
        print('STATUS CODE: ' + str(r.status_code))
       
# *******************************************************
    def move_routine(self, motion, axis, quantity):
        if motion == 'home':
            if axis == 'X, Y':
                home_data = {'command': 'home', 'axes': ['x', 'y']}
            elif axis == 'X':
                home_data = {'command': 'home', 'axes': ['x']}
            elif axis == 'Y':
                home_data = {'command': 'home', 'axes': ['y']}
            elif axis == 'Z':
                home_data = {'command': 'home', 'axes': ['z']}
            elif axis == 'X, Y, Z':
                home_data = {'command': 'home', 'axes': ['x', 'y', 'z']}
            else:
                print ("Home Error")    
            try:
                if debug:
                    print('[HOME ' + axis + '] Trying /API request to Octoprint...')
                r = requests.post(printheadurl, headers=headers, json=home_data, timeout=httptimeout)
                if debug:
                    print('[HOME ' + axis + '] STATUS CODE: ' + str(r.status_code))
            except requests.exceptions.RequestException as e:
                r = False
                if debug:
                    print('ERROR: Couldn\'t contact Octoprint /job API')
                    print(e)
        elif motion == 'jog':
                jog_data = {'command': 'jog', axis: quantity}
                print('JOGDATA: ' + str(jog_data))
                r = requests.post(printheadurl, headers=headers, json=jog_data, timeout=httptimeout)
                if debug:
                    print('STATUS CODE: ' + str(r.status_code))
        else:
            print ('error')

    def setup_routine(self):
        self.root.ids.file_list.clear_widgets()
        r = requests.get(filesapiurl, headers=headers, timeout=1)
        data = r.json()
        for i in data['files']:
            full_file_name = i['name']
            short_file_name = full_file_name[:25]
            print(short_file_name)
            self.root.ids.file_list.add_widget(
                OneLineListItem(
                    text=full_file_name,
                    #ids = full_file_name,
                    on_release = self.select_file
                )
            ) 

    def select_file (self, onelinelistitem):
        print ('file: ', onelinelistitem.text)
        file_data = {'command':'select', 'print': False}
        print(filesapiurl + '/local/' + onelinelistitem.text + str(file_data))
        r = requests.post(filesapiurl + '/local/' + onelinelistitem.text, headers=headers, json=file_data, timeout=httptimeout)
        print('STATUS CODE: ' + str(r.status_code))



    def build(self):
        # Temporarily overide the default screen size
        #self.theme_cls.primary_palette = "Green"
        Window.size = (480, 800)
        Window.borderless = True
        self.IP_address =get_ip(self)
        return self.run_routine ()

def get_ip(self):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
        print (IP)
        return IP

MainApp().run()

 