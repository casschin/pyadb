# Author: Chema Garcia (aka sch3m4)
# Contact: chema@safetybits.net | @sch3m4 | http://safetybits.net/contact 
# Homepage: http://safetybits.net
# Project Site: http://github.com/sch3m4/pyadb

import sys
import os
import subprocess


class ADB:
    PYADB_VERSION = "0.1.4"

    _output = None
    _error = None
    _return = 0
    _devices = None
    _target = None

    # reboot modes
    REBOOT_RECOVERY = 1
    REBOOT_BOOTLOADER = 2
    
    # default TCP/IP port
    DEFAULT_TCP_PORT = 5555
    # default TCP/IP host
    DEFAULT_TCP_HOST = "localhost"
    
    def pyadb_version(self):
        return self.PYADB_VERSION

    def __init__(self, adb_path=None):
        self.__adb_path = adb_path

    def __clean__(self):
        self._output = None
        self._error = None
        self._return = 0

    def __parse_output__(self,outstr):
        ret = None

        if len(outstr) > 0:
            ret = outstr.splitlines()

        return ret

    def __build_command__(self, cmd):
        ret = None

        if self._devices is not None and len(self._devices) > 1 and self._target is None:
            self._error = "Must set target device first"
            self._return = 1
            return ret

        # Modified function to directly return command set for Popen
        #
        # Unfortunately, there is something odd going on and the argument list is not being properly
        # converted to a string on the windows 7 test systems.  To accomodate, this block explitely
        # detects windows vs. non-windows and builds the OS dependent command output
        #
        # Command in 'list' format: Thanks to Gil Rozenberg for reporting the issue
        #
        if sys.platform.startswith('win'):
            ret = self.__adb_path + " "
            if self._target is not None:
                ret += "-s " + self._target + " "
            if type(cmd) is list:
                ret += ' '.join(cmd)
            else:
                ret += cmd
        else:
            ret = [self.__adb_path]
            if self._target is not None:
                ret += ["-s", self._target]
                
            if type(cmd) is list:
                for i in cmd:
                    ret.append(i)
            else:
                ret += [cmd]

        return ret
    
    def get_output(self):
        return self._output
    
    def get_error(self):
        return self._error

    def get_return_code(self):
        return self._return

    def lastFailed(self):
        """
        Did the last command fail?
        """
        if self._output is None and self._error is not None and self._return:
            return True
        return False

    def run_cmd(self,cmd):
        """
        Runs a command by using adb tool ($ adb <cmd>)
        """
        self.__clean__()

        if self.__adb_path is None:
            self._error = "ADB path not set"
            self._return = 1
            return
        
        # For compat of windows
        cmd_list = self.__build_command__(cmd)

        adb_proc = subprocess.Popen(
            cmd_list,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False
        )
        (self._output, self._error) = adb_proc.communicate()
        self._return = adb_proc.returncode

        if len(self._output) == 0:
            self._output = None

        if len(self._error) == 0:
            self._error = None

        return

    def get_version(self):
        """
        Returns ADB tool version
        adb version
        """
        self.run_cmd("version")
        try:
            ret = self._output.split()[-1:][0]
        except:
            ret = None
        return ret

    def check_path(self):
        """
        Intuitive way to verify the ADB path
        """
        if self.get_version() is None:
            return False
        return True

    def set_adb_path(self,adb_path):
        """
        Sets ADB tool absolute path
        """
        if os.path.isfile(adb_path) is False:
            return False
        self.__adb_path = adb_path
        return True

    def get_adb_path(self):
        """
        Returns ADB tool path
        """
        return self.__adb_path

    def start_server(self):
        """
        Starts ADB server
        adb start-server
        """
        self.__clean__()
        self.run_cmd('start-server')
        return self._output

    def kill_server(self):
        """
        Kills ADB server
        adb kill-server
        """
        self.__clean__()
        self.run_cmd('kill-server')

    def restart_server(self):
        """
        Restarts ADB server
        """
        self.kill_server()
        return self.start_server()

    def restore_file(self,file_name):
        """
        Restore device contents from the <file> backup archive
        adb restore <file>
        """
        self.__clean__()
        self.run_cmd(['restore' , file_name ])
        return self._output

    def wait_for_device(self):
        """
        Blocks until device is online
        adb wait-for-device
        """
        self.__clean__()
        self.run_cmd('wait-for-device')
        return self._output

    def get_help(self):
        """
        Returns ADB help
        adb help
        """
        self.__clean__()
        self.run_cmd('help')
        return self._output

    def get_devices(self):
        """
        Returns a list of connected devices
        adb devices
        """
        error = 0
        self.run_cmd('devices')
        if self._error is not None:
            return ''

        self._devices = self._output.decode().partition('\n')[2].replace('device', '').split()

        if self._devices[1:] == ['no', 'permissions']:
            error = 2
            self._devices = None

        return error, self._devices

    def set_target_device(self,device):
        """
        Select the device to work with
        """
        self.__clean__()
        if device is None or not device in self._devices:
            self._error = 'Must get device list first'
            self._return = 1
            return False
        self._target = device
        return True

    def get_target_device(self):
        """
        Returns the selected device to work with
        """
        return self._target

    def get_state(self):
        """
        Get ADB state
        adb get-state
        """
        self.__clean__()
        self.run_cmd('get-state')
        return self._output

    def get_serialno(self):
        """
        Get serialno from target device
        adb get-serialno
        """
        self.__clean__()
        self.run_cmd('get-serialno')
        return self._output

    def reboot_device(self,mode):
        """
        Reboot the target device
        adb reboot recovery/bootloader
        """
        self.__clean__()
        if not mode in (self.REBOOT_RECOVERY,self.REBOOT_BOOTLOADER):
            self._error = "mode must be REBOOT_RECOVERY/REBOOT_BOOTLOADER"
            self._return = 1
            return self._output
        self.run_cmd(["reboot", "%s" % "recovery" if mode == self.REBOOT_RECOVERY else "bootloader"])
        return self._output

    def set_adb_root(self):
        """
        restarts the adbd daemon with root permissions
        adb root
        """
        self.__clean__()
        self.run_cmd('root')
        return self._output

    def set_system_rw(self):
        """
        Mounts /system as rw
        adb remount
        """
        self.__clean__()
        self.run_cmd("remount")
        return self._output

    def get_remote_file(self,remote,local):
        """
        Pulls a remote file
        adb pull remote local
        """
        self.__clean__()
        self.run_cmd(['pull',remote , local] )

        if self._error is not None and "bytes in" in self._error:
            self._output = self._error
            self._error = None

        return self._output

    def push_local_file(self,local,remote):
        """
        Push a local file
        adb push local remote
        """
        self.__clean__()
        self.run_cmd(['push',local,remote] )
        return self._output

    def shell_command(self,cmd):
        """
        Executes a shell command
        adb shell <cmd>
        """
        self.__clean__()
        self.run_cmd(['shell',cmd])
        return self._output

    def listen_usb(self):
        """
        Restarts the adbd daemon listening on USB
        adb usb
        """
        self.__clean__()
        self.run_cmd("usb")
        return self._output

    def listen_tcp(self,port=DEFAULT_TCP_PORT):
        """
        Restarts the adbd daemon listening on the specified port
        adb tcpip <port>
        """
        self.__clean__()
        self.run_cmd(['tcpip',port])
        return self._output

    def get_bugreport(self):
        """
        Return all information from the device that should be included in a bug report
        adb bugreport
        """
        self.__clean__()
        self.run_cmd("bugreport")
        return self._output

    def get_jdwp(self):
        """
        List PIDs of processes hosting a JDWP transport
        adb jdwp
        """
        self.__clean__()
        self.run_cmd("jdwp")
        return self._output

    def get_logcat(self,lcfilter=""):
        """
        View device log
        adb logcat <filter>
        """
        self.__clean__()
        self.run_cmd(['logcat',lcfilter])
        return self._output

    def run_emulator(self,cmd=""):
        """
        Run emulator console command
        """
        self.__clean__()
        self.run_cmd(['emu',cmd])
        return self._output
    
    def connect_remote (self,host=DEFAULT_TCP_HOST,port=DEFAULT_TCP_PORT):
        """
        Connect to a device via TCP/IP
        adb connect host:port
        """
        self.__clean__()
        self.run_cmd(['connect',"%s:%s" % ( host , port ) ] )
        return self._output
    
    def disconnect_remote (self , host=DEFAULT_TCP_HOST , port=DEFAULT_TCP_PORT):
        """
        Disconnect from a TCP/IP device
        adb disconnect host:port
        """
        self.__clean__()
        self.run_cmd(['disconnect',"%s:%s" % ( host , port ) ] )
        return self._output
    
    def ppp_over_usb(self,tty=None,params=""):
        """
        Run PPP over USB
        adb ppp <tty> <params>
        """
        self.__clean__()
        if tty is None:
            return self._output
        
        cmd = ["ppp", tty]
        if params != "":
            cmd += params
            
        self.run_cmd(cmd)
        return self._output

    def sync_directory(self, directory=""):
        """
        Copy host->device only if changed (-l means list but don't copy)
        adb sync <dir>
        """
        self.__clean__()
        self.run_cmd(['sync', directory])
        return self._output
    
    def forward_socket(self, local=None,remote=None):
        """
        Forward socket connections
        adb forward <local> <remote>
        """
        self.__clean__()
        if local is None or remote is None:
            return self._output
        self.run_cmd(['forward',local,remote])
        return self._output


    def uninstall(self, package=None, keepdata=False):
        """
        Remove this app package from the device
        adb uninstall [-k] package
        """
        self.__clean__()
        if package is None:
            return self._output
        cmd = ['uninstall',"%s" % (package if keepdata is True else "-k %s" % package )]
        self.run_cmd(cmd)
        return self._output

    def install(self, fwdlock=False, reinstall=False, sdcard=False, pkgapp=None):
        """
        Push this package file to the device and install it
        adb install [-l] [-r] [-s] <file>
        -l -> forward-lock the app
        -r -> reinstall the app, keeping its data
        -s -> install on sdcard instead of internal storage
        """

        self.__clean__()
        if pkgapp is None:
            return self._output
        
        cmd = "install "
        if fwdlock is True:
            cmd += "-l "
        if reinstall is True:
            cmd += "-r "
        if sdcard is True:
            cmd += "-s "
        
        self.run_cmd([cmd,pkgapp])
        return self._output

    def find_binary(self, name=None):
        """
        Look for a binary file on the device
        """
        
        self.shell_command(['which',name])
        
        if self._output is None: # not found
            self._error = "'%s' was not found" % name
        elif self._output.strip() == "which: not found": # 'which' binary not available
            self._output = None
            self._error = "which binary not found"
        else:
            self._output = self._output.strip()

        return self._output
