#!/usr/bin/env python3

try:
    import sys
    import subprocess
    from os import popen as pipe
except ImportError as e:
    print("[!] Required module missing. %s" % e.args[0])
    sys.exit(-1)


class Fastboot(object):
    __fastboot_path = None
    __output = None
    __error = None
    __devices = None
    __target = None

    def __init__(self, fastboot_path="fastboot"):
        """
        By default we assume fastboot is in $PATH.
        Alternatively, the path to fasboot can be supplied.
        """
        self.__fastboot_path = fastboot_path
        if not self.check_path():
            self.__error = "[!] fastboot path not valid."

    def __clean__(self):
        self.__output = None
        self.__error = None

    def __read_output__(self, fd):
        ret = ""
        while 1:
            line = fd.readline()
            if not line:
                break
            ret += line

        if len(ret) == 0:
            ret = None

        return ret

    def __build_command__(self, cmd):
        """
        Build command parameters for Fastboot command
        """
        if self.__devices is not None and len(self.__devices) > 1 and self.__target is None:
            self.__error = "[!] Must set target device first"
            return None

        if type(cmd) is tuple:
            a = list(cmd)
        elif type(cmd) is list:
            a = cmd
        else:
            a = cmd.split(" ")
        a.insert(0, self.__fastboot_path)
        if self.__target is not None:
            # add target device arguments to the command
            a.insert(1, '-s')
            a.insert(2, self.__target)

        return a

    def run_cmd(self, cmd):
        """
        Run a command against the fastboot tool ($ fastboot <cmd>)
        """
        self.__clean__()

        if self.__fastboot_path is None:
            self.__error = "[!] Fastboot path not set"
            return False

        try:
            args = self.__build_command__(cmd)
            if args is None:
                return
            cmdp = subprocess.Popen(args, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            self.__output, self.__error = cmdp.communicate()
            retcode = cmdp.wait()
            return self.__output
        except OSError as error:
            self.__error = str(error)

        return

    def check_path(self):
        """
        Check if the Fastboot path is valid
        """
        if self.run_cmd("help") is None:
            print("[-] fastboot executable not found")
            return False
        return True

    def set_fastboot_path(self, fastboot_path):
        """
        Set the Fastboot tool path
        """
        self.__fastboot_path = fastboot_path
        self.check_path()

    def get_fastboot_path(self):
        """
        Returns the Fastboot tool path
        """
        return self.__fastboot_path_path

    # noinspection PyUnusedLocal
    def get_devices(self):
        """
        Return a dictionary of fastboot connected devices along with an incremented Id.
        fastboot devices
        """
        error = 0
        # Clear existing list of devices
        self.__devices = None
        self.run_cmd("devices")
        if self.__error is not None:
            return ''
        try:
            device_list = self.__output.replace('fastboot', '').split()

            if device_list[1:] == ['no', 'permissions']:
                error = 2
                self.__devices = None
        except:
            self.__devices = None
            return self.__devices
        i = 0
        device_dict = {}
        for device in device_list:
            # Add list to dictionary with incrementing ID
            device_dict[i] = device
            i += 1
        self.__devices = device_dict
        return self.__devices

    def set_target_by_name(self, device):
        """
        Specify the device name to target
        example: set_target_device('emulator-5554')
        """
        if device is None or device not in list(self.__devices.values()):
            self.__error = 'Must get device list first'
            print("[!] Device not found in device list")
            return False
        self.__target = device
        return "[+] Target device set: %s" % self.get_target_device()

    def set_target_by_id(self, device):
        """
        Specify the device ID to target.
        The ID should be one from the device list.
        """
        if device is None or device not in self.__devices:
            self.__error = 'Must get device list first'
            print("[!] Device not found in device list")
            return False
        self.__target = self.__devices[device]
        return "[+] Target device set: %s" % self.get_target_device()

    def get_target_device(self):
        """
        Returns the selected device to work with
        """
        if self.__target is None:
            print("[*] No device target set")

        return self.__target

    def flash_all(self, wipe=False):
        """
        flash boot + recovery + system. Optionally wipe everything
        """
        if wipe:
            self.run_cmd('-w flashall')
        else:
            self.run_cmd('flashall')

    def format(self, partition):
        """
        Format the specified partition
        """
        self.run_cmd('format %s' % partition)
        return self.__output

    def reboot_device(self):
        """
        Reboot the device normally
        """
        self.run_cmd('reboot')
        return self.__output

    def reboot_device_bootloader(self):
        """
        Reboot the device into bootloader
        """
        self.run_cmd('reboot-bootloader')
        return self.__output

    def oem_unlock(self):
        """
        unlock bootloader
        """
        self.run_cmd('oem unlock')
        return self.__output

    def oem_lock(self):
        """
        lock bootloader
        """
        self.run_cmd('oem lock')
        return self.__output
