#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import re
import subprocess
from datetime import datetime
import argparse
import ctypes
from bs4 import BeautifulSoup
import platform
from typing import Optional, List, Union
from collections import defaultdict

print('*****************************************************************')
print('*                     Tool: PC Info                             *')
print('*                  Version: v1.7.0                              *')
print('*             Release Date: 2025.07.12                          *')
print('*                   Author: Gavin.Xie                           *')
print('*****************************************************************')
print('\n')

'''
2025.07.12 Gavin.Xie v1.7.0, Add collect PC info for Linux system.
2025.07.07 Gavin.Xie v1.6.0, Add Battery Health and Battery cycle count to Battery_Info section.
2025.07.01 Gavin.Xie v1.5.0, Modify codes in systemInfo/batteryInfo/AppInfo section.
2025.05.01 Gavin.Xie v1.4.0, Modify codes in systemInfo/batteryInfo section.
2025.04.10 Gavin.Xie v1.3.0, Fix some issue when not have apps & products & device.
2025.03.28 Gavin.Xie v1.2.2, Add driver date info to driver section. Modify some codes.
2024.10.16 Gavin.Xie v1.2.1, Add tool version info to json file; Modify OS version display format.
2024.07.25 Gavin.Xie v1.2.1 Add Memory Vendor and more info to Memory section.
2023.1 Gavin.Xie v0.0.1 Add CPU,BIOS,RAM,System section.
'''
tool_name = 'PC Info'
tool_ver = '1.7.0'
release_date = '2025.07.12'
author = 'Gavin.Xie'

cwdp = os.getcwd()
pc_info_dic = {}
pc_info_dic['PC_Info Version'] = tool_ver
pc_info_dic['PC_Info Release'] = release_date
json_file_name = 'PC_Info_'
pc_info_items = ['system','bios','os','ram','cpu','disk','battery','video','panel','camera', \
                 'biometric','touchpad','keyboard','audio','network','app','driver']

def isAdmin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def runAdminCmd(command):
    ctypes.windll.shell32.ShellExecuteW(None, "runas", 'cmd.exe', fr"/c {command}", None, 1)
    
def runCmd(cmd):
    try:
        out, err = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, \
                                    encoding='gbk', shell=True).communicate()
        if err:
            print(err)
        return out, err
    except Exception as ex:
        print(ex)

def get_os_type():
    system = platform.system()
    if system == "Windows":
        return "Windows"
    elif system == "Linux":
        return "Linux"
    else:
        return "Other (e.g., macOS)"

def write_to_json():
    try:
        now = datetime.now()
        cur_date = str(now.date()).replace("-","")
        pc_info_json = os.path.abspath(os.path.join(cwdp, f'{json_file_name}{cur_date}.json'))
        content_json = json.dumps(pc_info_dic, ensure_ascii=False, indent=4)
        with open(pc_info_json, 'w', encoding='utf-8') as fw:
            fw.write(content_json)
        print(f'JSON file generation: {pc_info_json}')
    except Exception as ex:
        print(ex)

def parsAttibute():
    try:
        parser = argparse.ArgumentParser(description=f'{tool_name}')
        #parser.add_argument('-list', type=str, choices =pc_info_items, help=f'Show all attribute')
        parser.add_argument('-list',help=f'Show all attribute', action="store_true")
        parser.add_argument('-get', type=str, help=f'Example: PC_Info -get driver or PC_Info -get "cpu ram disk"')
        parser.add_argument('-version', action="store_true", help=f'Show version info')
        #parser.add_argument('-get', type=str, help=f'Attribute list: {pc_info_items} EX: PC_Info -get driver')
        args = parser.parse_args()
        return args
    except Exception as ex:
        print(ex)

class RegistryOperate:
    def __init__(self, reg_path):
        self.reg_path = reg_path

    def getFullKeyInfo(self, val_name):
        get_full_key_cmd = fr'powershell "Get-ItemProperty {self.reg_path} | select {val_name} | convertto-json"'
        rs, res = self.runRegCmd(get_full_key_cmd, 1)
        return rs, res

    def getRegValue(self, val_name):
        query_value_cmd = fr'reg query {self.reg_path} /v {val_name}'
        rs, res = self.runRegCmd(query_value_cmd, 0)
        return rs, res
    
    def setRegValue(self, val_name, val_type, val_data):
        set_value_cmd = fr'reg add {self.reg_path} /v {val_name} /t {val_type} /d {val_data} /f'
        if isAdmin():
            rs, res = self.runRegCmd(set_value_cmd, 0)
        else:
            runAdminCmd(set_value_cmd)

    def runRegCmd(self, cmd, out_type):
        try:
            out, err = runCmd(cmd)
            if err:
                msg = f'Run cmd occur error: {err}'
                return 1, msg
            else:
                if out:
                    if out_type:
                        out = json.loads(out)
                    return 0, out
                else:
                    msg = 'Output result is blank'
                    return 1, msg
        except Exception as ex:
            msg = f'Run cmd occur error: {ex}'
            return 1, msg

class Win32Wmi:
    def __init__(self):
        self.pw = 'Powershell "gcim win32_'

    def get_system_info(self):
        print('Check system info ...')
        cmd = self.pw + 'ComputerSystem'
        get_system_cmd = ' '.join([cmd, '|','select Manufacturer,Model,Name,OEMStringArray,SystemType',
                                   '|', 'convertto-json', '"'])
        self.get_item_result('system', get_system_cmd)

    def get_os_info(self):
        print('Check OS info ...')
        os_info_dic = {}
        cmd = self.pw + 'OperatingSystem'
        get_os_cmd = ' '.join([cmd, '|','select Caption','|', 'convertto-json', '"'])
        get_os_ver = 'ver'
        for i in (get_os_cmd, get_os_ver):
            out, err = runCmd(i)
            if 'gcim' in i:
                out = json.loads(out)
                os_info_dic['OS_Caption'] = out['Caption']
            else:
                os_version = re.search(fr'\d+.\d+.\d+.\d+', out).group()
                os_info_dic['OS_Version'] = os_version
        pc_info_dic['OS Info'] = os_info_dic
        print(f'{os_info_dic}\n')

    def get_bios_info(self):
        print('Check BIOS info ...')
        cmd = self.pw + 'bios'
        get_bios_cmd = ' '.join([cmd, '|','select Manufacturer,SMBIOSBIOSVersion,SerialNumber',
                                   '|', 'convertto-json', '"'])
        self.get_item_result('bios', get_bios_cmd)

    def get_ram_info(self):
        print('Check Memory info ...')
        ram_vendor_name = ["kingston","adata","micron","hynix","samsung","qimonda", "sk hynix"]
        ram_vendor_id = {"0198":"Kingston","04CB":"ADATA","2C00":"Micron","802C":"Micron","AD00":"Hynix", \
                        "80AD":"Hynix","80CE":"Samsung","CE00":"Samsung","5105":"Qimonda","8551":"Qimonda"}
        cmd = self.pw + 'PhysicalMemory'
        get_ram_cmd = ' '.join([cmd, '|','select PartNumber,SerialNumber,Tag,Manufacturer,\
                        Capacity,DataWidth,MemoryType,TotalWidth,Speed,ConfiguredClockSpeed,ConfiguredVoltage,\
                        DeviceLocator,MaxVoltage,MinVoltage', '|', 'convertto-json', '"'])
        out, err = runCmd(get_ram_cmd)
        if not out:
            out = 'Not found memory info'
        else:
            out = json.loads(out)
        total_size = 0
        verdor = ""
        if isinstance(out, list) == True:
            n = len(out)
            for i in range(n):
                size = 0
                size = str(int(out[i]['Capacity'] / 1024 / 1024 / 1024)) + 'GB'
                out[i]['size'] = size
                total_size += out[i]['Capacity']
                ram_flag = 0
                if out[i]['Manufacturer'].lower() not in ram_vendor_name:
                    for k, v in ram_vendor_id.items():
                        #if k in out[i]['Manufacturer']:
                        if k == out[i]['Manufacturer'][0:4]:
                            out[i]['Vendor'] = v
                            ram_flag = 1
                    if not ram_flag:
                        out[i]['Vendor'] = 'Other'
                else:
                    out[i]['Vendor'] = out[i]['Manufacturer']
            total_size = str(int(total_size / 1024 / 1024 / 1024)) + 'GB'
            for i in range(n):
                out[i]['total_size'] = total_size
        else:
            total_size = str(int(out['Capacity'] / 1024 / 1024 / 1024)) + 'GB'
            out['total_size'] = total_size
            ram_flag = 0
            if out['Manufacturer'].lower() not in ram_vendor_name:
                for k, v in ram_vendor_id.items():
                    #if k in out[i]['Manufacturer']:
                    if k == out['Manufacturer'][0:4]:
                        out['Vendor'] = v
                        ram_flag = 1
                if not ram_flag:
                    out['Vendor'] = 'Other'
            else:
                out['Vendor'] = out['Manufacturer']
        print(f'Total_size={total_size}')
        print(f'{out}\n')
        pc_info_dic['RAM Info'] = out

    def get_cpu_info(self):
        print('Check Processor info ...')
        cmd = self.pw + 'Processor'
        get_cpu_cmd = ' '.join([cmd, '|','select Caption,Name,Manufacturer, \
                        SocketDesignation,CurrentClockSpeed,MaxClockSpeed,CurrentVoltage, \
                        L2CacheSize', '|', 'convertto-json', '"'])
        self.get_item_result('CPU', get_cpu_cmd)

    def get_disk_info(self):
        print('Check Disk info ...')
        cmd = self.pw + 'diskdrive'
        get_disk_cmd = ' '.join([cmd, '|','select Model,Size,Firmwarerevision,InterfaceType,MediaType',
                                 '|', 'convertto-json', '"'])
        self.get_item_result('disk', get_disk_cmd)

    def get_battery_info(self):
        print('Check Battery info ...')
        cmd = self.pw + 'battery'
        get_battery_cmd = ' '.join([cmd, '|','select Caption,Name,DeviceID,BatteryStatus,EstimatedChargeRemaining',
                                 '|', 'convertto-json', '"'])
        out, err = runCmd(get_battery_cmd)
        if not out:
            out = 'Not found battery info'
        else:
            out = json.loads(out)
            cmd = self.pw + 'PortableBattery'
            get_portable_battery_cmd = ' '.join([cmd, '|','select DesignCapacity, \
                                    DesignVoltage,CapacityMultiplier,Location,ManufactureDate,Manufacturer',
                                    '|', 'convertto-json', '"'])
            out1, err1 = runCmd(get_portable_battery_cmd)
            if not out1:
                out1 = 'Not found portable battery info'
            else:
                print(f'run portable battery cmd')
                out1 = json.loads(out1)
                out.update(out1)
            runCmd('powercfg /batteryreport')
            with open('battery-report.html', 'r', encoding='utf-8') as fr:
                html_info = fr.read()
            os.remove('battery-report.html')
            #shutil.rmtree('battery-report.html')
            soup = BeautifulSoup(html_info, 'html.parser')
            design_capacity = soup.find('td', string='DESIGN CAPACITY').find_next_sibling('td').get_text(strip=True)
            full_charge_capacity = soup.find('td', string='FULL CHARGE CAPACITY').find_next_sibling('td').get_text(strip=True)
            cycle_count = soup.find('td', string='CYCLE COUNT').find_next_sibling('td').get_text(strip=True)

            design_value = int(design_capacity.replace('mWh', '').replace(',', '').strip())
            full_charge_value = int(full_charge_capacity.replace('mWh', '').replace(',', '').strip())
            health_percent = f'{round((full_charge_value / design_value) * 100, 2)}%'
            battery_health_result = {"Battery Health":health_percent, "Cycle Count": cycle_count}
            batter_heal_json = json.dumps(battery_health_result)
            batter_heal_json = json.loads(batter_heal_json)
            out.update(batter_heal_json)
            print(f'{out}\n')

        pc_info_dic['Battery Info'] = out

    def get_video_info(self):
        print('Check Video info ...')
        cmd = self.pw + 'videocontroller'
        get_video_cmd = ' '.join([cmd, '|','select Name,DeviceID,CurrentHorizontalResolution, \
                        CurrentVerticalResolution,CurrentNumberOfColors,CurrentRefreshRate,MaxRefreshRate,\
                        MinRefreshRate,VideoModeDescription,VideoProcessor,AdapterCompatibility,AdapterDACType, \
                        DriverVersion','|', 'convertto-json', '"'])
        self.get_item_result('video', get_video_cmd)

    def get_audio_info(self):
        print('Check Audio info ...')
        cmd = self.pw + 'PnpEntity'
        get_audio_cmd = ' '.join([cmd, '|','where pnpclass -match "MEDIA"','|',
                                  'select Caption,Description,Status,ConfigManagerErrorCode,\
                        DeviceID,HardwareID,Manufacturer','|', 'convertto-json', '"'])
        self.get_item_result('audio', get_audio_cmd)

    def get_panel_info(self):
        print('Check Panel info ...')
        cmd = self.pw + 'DesktopMonitor'
        get_panel_cmd = ' '.join([cmd, '|','select DeviceID,Name,\
                        PixelsPerXLogicalInch,PixelsPerYLogicalInch,Status,ConfigManagerErrorCode,\
                        PNPDeviceID,MonitorManufacturer','|', 'convertto-json', '"'])
        self.get_item_result('panel', get_panel_cmd)

    def get_camera_info(self):
        print('Check Camera info ...')
        cmd = self.pw + 'PnpEntity'
        get_camera_cmd = ' '.join([cmd, '|','where pnpclass -match "camera"','|',
                                  'select Caption,Description,Status,ConfigManagerErrorCode,DeviceID, \
                        HardwareID,Manufacturer,Service', '|','convertto-json', '"'])
        self.get_item_result('camera', get_camera_cmd)
    
    def get_touchpad_info(self):
        print('Check Touchpad info ...')
        cmd = self.pw + 'PnpEntity'
        get_touchpad_cmd = ' '.join([cmd, '|','where pnpclass -match "HIDCLASS"','|',
                                  'select Caption,Description,Status,ConfigManagerErrorCode,\
                            DeviceID,HardwareID,Manufacturer', '|','convertto-json', '"'])
        self.get_item_result('touchpad', get_touchpad_cmd)

    def get_biometric_info(self):
        print('Check Biometric info ...')
        cmd = self.pw + 'PnpEntity'
        get_biometric_cmd = ' '.join([cmd, '|','where pnpclass -match "biometric"','|',
                                  'select Caption,Description,Status,ConfigManagerErrorCode,\
                            DeviceID,HardwareID,Manufacturer,Service', '|','convertto-json', '"'])
        self.get_item_result('biometric', get_biometric_cmd)

    def get_keyboard_info(self):
        print('Check Keyboard info ...')
        cmd = self.pw + 'PnpEntity'
        get_Keyboard_cmd = ' '.join([cmd, '|','where pnpclass -match "keyboard"','|',
                                  'select Caption,Description,Status,ConfigManagerErrorCode,\
                            DeviceID,HardwareID,Manufacturer,Service', '|','convertto-json', '"'])
        self.get_item_result('keyboard', get_Keyboard_cmd)

    def get_network_info(self):
        print('Check Network info ...')
        cmd = self.pw + 'PnpEntity'
        get_network_cmd = ' '.join([cmd, '|','where pnpclass -match "Net"','|',
                                  'select Caption,Description,Status,ConfigManagerErrorCode,\
                            DeviceID,HardwareID,Manufacturer,Service', '|','convertto-json', '"'])
        self.get_item_result('network', get_network_cmd)

    # def product_info(self):
    #     print('Check Apps info ...')
    #     cmd = self.pw + 'product'
    #     get_product_cmd = ' '.join([cmd, '|','select','Name,Vendor,Version,InstallDate', 
    #                                 '|','convertto-json', '"'])
    #     self.get_item_result('apps', get_product_cmd)

    def get_app_info(self):
        print('Check Apps info ...')
        reg_path_32 = fr'HKLM:\Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*'
        reg_path_64 = fr'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*'
        # sel_object = 'DisplayName, DisplayVersion,InstallDate,Publisher,UninstallString'
        sel_object = 'DisplayName, DisplayVersion,Publisher,InstallDate'
        need_uninstall_sw_list = []
        sw_list = []
        for reg_path in (reg_path_32, reg_path_64):
            reg_obj = RegistryOperate(reg_path)
            rs, res = reg_obj.getFullKeyInfo(sel_object)
            if rs:
                msg = f'occur error: {res}'
            else:
                for sw in res:
                    sw_list.append(sw)
        pc_info_dic[fr'App Info'] = sw_list
        print(sw_list)

    def get_driver_info(self):
        print('Check Driver info ...')
        cmd = self.pw + 'pnpsigneddriver'
        get_drive_cmd = ' '.join([cmd, '|','select','description, driverversion, @{Name=\'driverdate\';\
                                     Expression={$_.driverdate.ToString(\'yyyy-MM-dd\')}}', 
                                    '|','convertto-json', '"'])
        self.get_item_result('driver', get_drive_cmd)

    def get_item_result(self,item, cmd):
        global json_file_name
        out, err = runCmd(cmd)
        if not out:
            print(f'Not found: {item} information')
        else:
            out = json.loads(out)
            if item == 'system':
                oem_str = out['OEMStringArray']
                if len(oem_str) > 1:
                    system_id = oem_str[1]
                    system_id = system_id[2:6]
                    out['system_id'] = system_id
                    del out['OEMStringArray']
                else:
                    system_id = oem_str[0]
                str1 = f'{str(out["Model"])}_{str(system_id)}_'
                json_file_name += str1
            elif item == 'bios':
                json_file_name += f'{out["SerialNumber"]}_'
            elif item == 'disk':
                if isinstance(out, list) == True:
                    n = len(out)
                    for i in range(n):
                        disk_size = str(int(out[i]['Size'] / 1000 / 1000 / 1000)) + 'GB'
                        out[i]['disk_size'] = disk_size
                else:   
                    disk_size = str(int(out['Size'] / 1000 / 1000 / 1000)) + 'GB'
                    out['disk_size'] = disk_size
            elif item == 'touchpad':
                # out = [i for i in out if "touch pad" or '触摸板' in i["Caption"]]
                out = [i for i in out if "touch pad" in i["Caption"] or '触摸板' in i["Caption"]]
                if len(out) == 1:
                    for i in out:
                        out = i
            elif item == 'network':
                if len(out) > 1:
                    out = [i for i in out if "WAN Miniport" not in i["Description"]]
                    if not out:
                        msg = 'Not find network info'
                        out = msg
            pc_info_dic[fr'{item.capitalize()} Info'] = out
            print(f'{out}\n')

class LinuxOS:
    # 查看内核识别的输入设备
    # cat / proc / bus / input / devices
    def run_command(self, cmd: str) -> Optional[str]:
        """执行命令并返回输出"""
        try:
            return subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode().strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

    def get_file_content(self, filepath: str) -> Optional[str]:
        """读取文件内容"""
        try:
            with open(filepath, 'r') as f:
                return f.read().strip()
        except (FileNotFoundError, PermissionError):
            return None

    # def get_system_info(self) -> dict[str, str]:
    def get_system_info(self):
        """获取系统基本信息"""
        pc_info_dic['system_info'] = {
            "hostname": platform.node(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "architecture": platform.architecture()[0],
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "uptime": self.get_uptime(),
            "last_boot": self.get_last_boot(),
            "timezone": self.get_timezone(),
            "locale": self.get_locale()
        }

    def get_uptime(self) -> str:
        """获取系统运行时间"""
        uptime_seconds = float(self.get_file_content('/proc/uptime').split()[0])
        days, remainder = divmod(uptime_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(days)}d {int(hours)}h {int(minutes)}m"

    def get_last_boot(self) -> Optional[str]:
        """获取最后启动时间"""
        return self.run_command("who -b | awk '{print $3, $4}'")

    def get_timezone(self) -> Optional[str]:
        """获取时区信息"""
        if os.path.exists('/etc/timezone'):
            return self.get_file_content('/etc/timezone')
        return self.run_command("timedatectl | grep 'Time zone' | awk '{print $3}'")

    def get_locale(self):
        """获取本地化设置"""
        locale_info = {}
        for var in ['LANG', 'LC_ALL', 'LC_CTYPE']:
            locale_info[var] = os.getenv(var, 'Not set')
        return locale_info

    def get_os_info(self):
        """获取操作系统信息"""
        os_info = {}
        if os.path.exists('/etc/os-release'):
            with open('/etc/os-release', 'r') as f:
                for line in f:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        os_info[key.lower()] = value.strip('"')
        pc_info_dic['os_info'] = os_info

    def get_bios_info(self):
        """获取BIOS信息"""
        bios = {}
        dmi_path = '/sys/class/dmi/id/'
        fields = {
            'bios_vendor': 'vendor',
            'bios_version': 'version',
            'bios_date': 'date',
            'bios_release': 'release',
            'product_name': 'product',
            'product_version': 'product_version',
            'product_serial': 'serial',
            'product_uuid': 'uuid'
        }
        
        for file, key in fields.items():
            content = self.get_file_content(f"{dmi_path}{file}")
            if content:
                bios[key] = content
        pc_info_dic['bios_info'] = bios

    def get_cpu_info(self):
        """获取CPU信息"""
        cpu_info = {
            "model": "Unknown",
            "cores": 0,
            "threads": 0,
            "architecture": platform.machine(),
            "cpus": []
        }
        
        # 获取/proc/cpuinfo内容
        cpuinfo = self.get_file_content('/proc/cpuinfo')
        if cpuinfo:
            processors = re.split(r'\n\n', cpuinfo)
            cpu_info["cores"] = len([p for p in processors if 'processor' in p])
            
            for proc in processors:
                if not proc:
                    continue
                cpu_data = {}
                for line in proc.split('\n'):
                    if ':' in line:
                        key, val = line.split(':', 1)
                        cpu_data[key.strip()] = val.strip()
                if cpu_data:
                    cpu_info["cpus"].append(cpu_data)
            
            if cpu_info["cpus"]:
                cpu_info["model"] = cpu_info["cpus"][0].get('model name', 'Unknown')
                cpu_info["threads"] = len(cpu_info["cpus"])
        
        # 获取CPU使用率
        cpu_usage = self.run_command("top -bn1 | grep 'Cpu(s)' | sed 's/.*, *\\([0-9.]*\\)%* id.*/\\1/' | awk '{print 100 - $1\"%\"}'")
        if cpu_usage:
            cpu_info["usage"] = cpu_usage
        
        # 获取CPU频率
        cpu_freq = self.get_file_content('/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq')
        if cpu_freq:
            cpu_info["current_frequency"] = f"{int(cpu_freq) // 1000} MHz"
        
        pc_info_dic['cpu_info'] = cpu_info

    def get_video_info(self):
        """获取GPU信息"""
        video_info = {
            "gpus": [],
            "nvidia": {},
            "amd": {},
            "intel": {}
        }
        
        # 使用lspci获取GPU信息
        lspci_output = self.run_command("lspci -nn | grep -i 'vga\\|3d\\|display'")
        if lspci_output:
            video_info["gpus"] = lspci_output.split('\n')
        
        # NVIDIA GPU信息
        nvidia_smi = self.run_command("nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader")
        if nvidia_smi:
            video_info["nvidia"] = {
                "driver": self.run_command("nvidia-smi --query-gpu=driver_version --format=csv,noheader"),
                "gpus": nvidia_smi.split('\n')
            }
        
        pc_info_dic['video'] = video_info

    def get_audio_info(self):
        """获取音频设备信息"""
        # return {
        #     "playback_devices": self.run_command("aplay -l").split('\n') if self.run_command("which aplay") else [],
        #     "recording_devices": self.run_command("arecord -l").split('\n') if self.run_command("which arecord") else []
        # }
        pc_info_dic['audio_info'] = {
            "playback_devices": self.run_command("aplay -l").split('\n') if self.run_command("which aplay") else [],
            "recording_devices": self.run_command("arecord -l").split('\n') if self.run_command("which arecord") else []
        }

    def get_panel_info(self):
        """获取显示信息"""
        # return {
        #     "panel": self.run_command("xrandr").split('\n') if self.run_command("which xrandr") else [],
        #     "edid": self.run_command("find /sys/devices -name edid | xargs cat | parse-edid").split('\n') if self.run_command("which parse-edid") else []
        # }
        pc_info_dic['panel_info'] = {
            "panel": self.run_command("xrandr").split('\n') if self.run_command("which xrandr") else [],
            "edid": self.run_command("find /sys/devices -name edid | xargs cat | parse-edid").split(
                '\n') if self.run_command("which parse-edid") else []
        }

    def get_camera_info(self):
        # 获取所有视频设备
        video_devices = [f for f in os.listdir('/dev') if f.startswith('video')]

        if not video_devices:
            pc_info_dic['camera_info'] = 'Not found camera info'
            return

        camera_info_list = []

        for device in video_devices:
            device_path = f"/dev/{device}"
            info = {'device': device_path}

            # 使用udevadm获取设备信息
            try:
                udevadm_output = subprocess.check_output(
                    ['udevadm', 'info', '--query=all', '--name=' + device_path],
                    stderr=subprocess.STDOUT
                ).decode('utf-8')

                # 解析udevadm输出
                for line in udevadm_output.split('\n'):
                    if 'ID_VENDOR=' in line:
                        info['vendor'] = line.split('=')[1].strip()
                    elif 'ID_VENDOR_ID=' in line:
                        info['vid'] = line.split('=')[1].strip()
                    elif 'ID_MODEL_ID=' in line:
                        info['pid'] = line.split('=')[1].strip()
                    elif 'ID_REVISION=' in line:
                        info['firmware_revision'] = line.split('=')[1].strip()
                    elif 'ID_MODEL=' in line:
                        info['model'] = line.split('=')[1].strip()
                    elif 'ID_SERIAL=' in line:
                        info['serial'] = line.split('=')[1].strip()

                # 获取硬件ID
                hwid = subprocess.check_output(
                    ['udevadm', 'info', '--query=property', '--name=' + device_path]
                ).decode('utf-8')

                hwid_match = re.search(r'ID_PATH=(.*)', hwid)
                if hwid_match:
                    info['hwid'] = hwid_match.group(1).strip()

            except subprocess.CalledProcessError as e:
                print(f"获取设备 {device_path} 信息时出错: {e.output}")
                continue

            # 使用v4l2-ctl获取更多信息
            try:
                v4l2_output = subprocess.check_output(
                    ['v4l2-ctl', '--device=' + device_path, '--all'],
                    stderr=subprocess.STDOUT
                ).decode('utf-8')

                # 解析v4l2-ctl输出
                for line in v4l2_output.split('\n'):
                    if 'Driver name' in line:
                        info['driver'] = line.split(':')[1].strip()
                    elif 'Bus info' in line:
                        info['bus_info'] = line.split(':')[1].strip()
                    elif 'Driver version' in line:
                        info['driver_version'] = line.split(':')[1].strip()

            except subprocess.CalledProcessError as e:
                print(f"使用v4l2-ctl获取设备 {device_path} 信息时出错: {e.output}")

            camera_info_list.append(info)

        pc_info_dic['camera_info'] = camera_info_list

    def get_touchpad_info(self):
        # 使用xinput获取所有输入设备
        try:
            xinput_output = subprocess.check_output(['xinput', '--list'], stderr=subprocess.STDOUT).decode('utf-8')
        except subprocess.CalledProcessError as e:
            print(f"执行xinput命令时出错: {e.output}")
            return []

        # 识别触摸板设备
        touchpad_devices = []
        for line in xinput_output.split('\n'):
            if 'TouchPad' in line or 'Touchpad' in line or 'Synaptics' in line or 'ETPS/2' in line:
                match = re.search(r'id=(\d+)', line)
                if match:
                    device_id = match.group(1)
                    device_name = line.split('\t')[0].strip()
                    touchpad_devices.append({'id': device_id, 'name': device_name})

        if not touchpad_devices:
            pc_info_dic['touchpad_info'] = 'Not found touchpad info'
            return

        touchpad_info_list = []

        for device in touchpad_devices:
            info = {
                'id': device['id'],
                'name': device['name'],
                'type': 'touchpad'
            }

            # 获取设备属性
            try:
                prop_output = subprocess.check_output(
                    ['xinput', '--list-props', device['id']],
                    stderr=subprocess.STDOUT
                ).decode('utf-8')

                # 解析设备属性
                for line in prop_output.split('\n'):
                    if 'Device Node' in line:
                        device_node = line.split(':')[-1].strip().strip('"')
                        info['device_node'] = device_node
                        break
            except subprocess.CalledProcessError as e:
                print(f"获取设备 {device['id']} 属性时出错: {e.output}")
                continue

            # 如果有设备节点，使用udevadm获取更多信息
            if 'device_node' in info:
                try:
                    udevadm_output = subprocess.check_output(
                        ['udevadm', 'info', '--query=all', '--name=' + info['device_node']],
                        stderr=subprocess.STDOUT
                    ).decode('utf-8')

                    # 解析udevadm输出
                    for line in udevadm_output.split('\n'):
                        if 'ID_VENDOR=' in line:
                            info['vendor'] = line.split('=')[1].strip()
                        elif 'ID_VENDOR_ID=' in line:
                            info['vid'] = line.split('=')[1].strip()
                        elif 'ID_MODEL_ID=' in line:
                            info['pid'] = line.split('=')[1].strip()
                        elif 'ID_REVISION=' in line:
                            info['firmware_revision'] = line.split('=')[1].strip()
                        elif 'ID_MODEL=' in line:
                            info['model'] = line.split('=')[1].strip()
                        elif 'ID_SERIAL=' in line:
                            info['serial'] = line.split('=')[1].strip()

                    # 获取硬件ID
                    hwid = subprocess.check_output(
                        ['udevadm', 'info', '--query=property', '--name=' + info['device_node']]
                    ).decode('utf-8')

                    hwid_match = re.search(r'ID_PATH=(.*)', hwid)
                    if hwid_match:
                        info['hwid'] = hwid_match.group(1).strip()

                except subprocess.CalledProcessError as e:
                    print(f"获取设备 {info['device_node']} 信息时出错: {e.output}")
                    continue

            # 对于PS/2设备，尝试从/sys获取信息
            if 'device_node' not in info or 'vid' not in info:
                try:
                    # 查找输入设备在/sys中的路径
                    input_devices = os.listdir('/sys/class/input/')
                    for input_dev in input_devices:
                        if input_dev.startswith('input'):
                            name_path = f"/sys/class/input/{input_dev}/device/name"
                            if os.path.exists(name_path):
                                with open(name_path, 'r') as f:
                                    name = f.read().strip()
                                    if name.lower() in info['name'].lower():
                                        # 找到匹配的设备
                                        device_path = f"/sys/class/input/{input_dev}/device"
                                        modalias_path = f"{device_path}/modalias"
                                        if os.path.exists(modalias_path):
                                            with open(modalias_path, 'r') as mf:
                                                modalias = mf.read().strip()
                                                # 解析modalias获取VID/PID
                                                match = re.search(r'i2c:(\w{4}):(\w{4})', modalias)
                                                if match:
                                                    info['vid'] = match.group(1)
                                                    info['pid'] = match.group(2)
                                                match = re.search(r'input:b(\w{4})v(\w{4})p(\w{4})', modalias)
                                                if match:
                                                    info['vid'] = match.group(2)
                                                    info['pid'] = match.group(3)

                                        # 尝试获取固件版本
                                        fw_path = f"{device_path}/firmware_version"
                                        if os.path.exists(fw_path):
                                            with open(fw_path, 'r') as fw:
                                                info['firmware_revision'] = fw.read().strip()
                                        break
                except Exception as e:
                    print(f"从/sys获取信息时出错: {e}")

            touchpad_info_list.append(info)

        pc_info_dic['touchpad_info'] = touchpad_info_list

    def get_keyboard_info(self):
        # 方法1: 使用xinput获取键盘设备
        keyboard_devices = []
        try:
            xinput_output = subprocess.check_output(['xinput', '--list'], stderr=subprocess.STDOUT).decode('utf-8')
            for line in xinput_output.split('\n'):
                if 'keyboard' in line.lower() and 'virtual' not in line.lower():
                    match = re.search(r'id=(\d+)', line)
                    if match:
                        device_id = match.group(1)
                        device_name = line.split('\t')[0].strip()
                        keyboard_devices.append({'id': device_id, 'name': device_name, 'source': 'xinput'})
        except subprocess.CalledProcessError as e:
            print(f"执行xinput命令时出错: {e.output}")

        # 方法2: 从/sys/class/input获取键盘设备
        # try:
        #     input_devices = os.listdir('/sys/class/input/')
        #     for input_dev in input_devices:
        #         if input_dev.startswith('input'):
        #             name_path = f"/sys/class/input/{input_dev}/device/name"
        #             if os.path.exists(name_path):
        #                 with open(name_path, 'r') as f:
        #                     name = f.read().strip().lower()
        #                     if 'keyboard' in name or 'keyboard' in input_dev.lower():
        #                         event_path = f"/dev/input/{input_dev}"
        #                         if os.path.exists(event_path):
        #                             keyboard_devices.append({
        #                                 'id': input_dev,
        #                                 'name': name,
        #                                 'device_node': event_path,
        #                                 'source': 'sysfs'
        #                             })
        # except Exception as e:
        #     print(f"从/sys/class/input获取信息时出错: {e}")

        if not keyboard_devices:
            pc_info_dic['keyboard_info'] = 'Not found Keyboard info'
            return

        keyboard_info_list = []

        for device in keyboard_devices:
            info = {
                'id': device['id'],
                'name': device['name'],
                'type': 'keyboard',
                'source': device['source']
            }

            # 获取设备节点（如果还没有）
            if 'device_node' not in device and device['source'] == 'xinput':
                try:
                    prop_output = subprocess.check_output(
                        ['xinput', '--list-props', device['id']],
                        stderr=subprocess.STDOUT
                    ).decode('utf-8')

                    for line in prop_output.split('\n'):
                        if 'Device Node' in line:
                            device_node = line.split(':')[-1].strip().strip('"')
                            info['device_node'] = device_node
                            break
                except subprocess.CalledProcessError as e:
                    print(f"获取设备 {device['id']} 属性时出错: {e.output}")
                    continue

            # 使用udevadm获取设备信息
            if 'device_node' in info:
                try:
                    udevadm_output = subprocess.check_output(
                        ['udevadm', 'info', '--query=all', '--name=' + info['device_node']],
                        stderr=subprocess.STDOUT
                    ).decode('utf-8')

                    # 解析udevadm输出
                    for line in udevadm_output.split('\n'):
                        if 'ID_VENDOR=' in line:
                            info['vendor'] = line.split('=')[1].strip()
                        elif 'ID_VENDOR_ID=' in line:
                            info['vid'] = line.split('=')[1].strip()
                        elif 'ID_MODEL_ID=' in line:
                            info['pid'] = line.split('=')[1].strip()
                        elif 'ID_REVISION=' in line:
                            info['firmware_revision'] = line.split('=')[1].strip()
                        elif 'ID_MODEL=' in line:
                            info['model'] = line.split('=')[1].strip()
                        elif 'ID_SERIAL=' in line:
                            info['serial'] = line.split('=')[1].strip()

                    # 获取硬件ID
                    hwid = subprocess.check_output(
                        ['udevadm', 'info', '--query=property', '--name=' + info['device_node']]
                    ).decode('utf-8')

                    hwid_match = re.search(r'ID_PATH=(.*)', hwid)
                    if hwid_match:
                        info['hwid'] = hwid_match.group(1).strip()

                except subprocess.CalledProcessError as e:
                    print(f"获取设备 {info['device_node']} 信息时出错: {e.output}")

            # 对于没有通过udevadm获取到VID/PID的设备，尝试从/sys获取
            if ('vid' not in info or 'pid' not in info) and device['source'] == 'sysfs':
                try:
                    modalias_path = f"/sys/class/input/{device['id']}/device/modalias"
                    if os.path.exists(modalias_path):
                        with open(modalias_path, 'r') as mf:
                            modalias = mf.read().strip()
                            # 解析modalias获取VID/PID
                            match = re.search(r'input:b(\w{4})v(\w{4})p(\w{4})', modalias)
                            if match:
                                info['vid'] = match.group(2)
                                info['pid'] = match.group(3)

                    # 尝试获取固件版本
                    fw_path = f"/sys/class/input/{device['id']}/device/firmware_version"
                    if os.path.exists(fw_path):
                        with open(fw_path, 'r') as fw:
                            info['firmware_revision'] = fw.read().strip()

                    # 尝试获取厂商信息
                    vendor_path = f"/sys/class/input/{device['id']}/device/vendor"
                    if os.path.exists(vendor_path):
                        with open(vendor_path, 'r') as vf:
                            info['vendor'] = vf.read().strip()

                except Exception as e:
                    print(f"从/sys获取额外信息时出错: {e}")

            keyboard_info_list.append(info)

        pc_info_dic['keyboard_info'] = keyboard_info_list

    def get_network_info(self):
        """获取网络信息"""
        pc_info_dic['network_info'] = {
            "interfaces": self.run_command("ip -o link show | awk '{print $2}'").replace(':', '').split('\n'),
            "ip_addresses": self.run_command("ip -o addr show | awk '{print $2, $4}'").split('\n'),
            "wireless": self.run_command("iw dev").split('\n') if self.run_command("which iw") else [],
            # "ethernet": self.run_command("ethtool eth0").split('\n') if self.run_command("which ethtool") else [],
            "ethernet": self.run_command("ethtool eth0") if self.run_command("which ethtool") else [],
            "routing": self.run_command("ip route").split('\n'),
            "dns": {
                "resolv.conf": self.get_file_content('/etc/resolv.conf'),
                "systemd_resolved": self.run_command("systemd-resolve --status")
            }
        }

    def get_battery_info(self):
        """获取电池信息"""
        battery = {}
        bat_path = '/sys/class/power_supply/BAT0/'
        if os.path.exists(bat_path):
            battery["capacity"] = self.get_file_content(f"{bat_path}capacity") + "%"
            battery["status"] = self.get_file_content(f"{bat_path}status")
            battery["technology"] = self.get_file_content(f"{bat_path}technology")
            battery["voltage"] = self.get_file_content(f"{bat_path}voltage_now")
            if battery["voltage"]:
                battery["voltage"] = f"{int(battery['voltage']) // 1000} mV"
        
        pc_info_dic['battery_info'] = battery

    def get_ram_info(self):
        """获取内存信息"""
        meminfo = {}
        mem_data = self.get_file_content('/proc/meminfo')
        if mem_data:
            for line in mem_data.split('\n'):
                if ':' in line:
                    key, val = line.split(':', 1)
                    meminfo[key.strip()] = val.strip()
        
        pc_info_dic['ram_info'] = meminfo

    def get_disk_info(self):
        """获取存储信息"""
        pc_info_dic['disk_info'] = {
            "disks": self.run_command("lsblk -o NAME,SIZE,TYPE,MOUNTPOINT").split('\n'),
            "partitions": self.run_command("df -h").split('\n'),
            "fstab": self.get_file_content('/etc/fstab'),
            "smart": self.run_command("smartctl --scan").split('\n') if self.run_command("which smartctl") else []
        }

    def get_app_info(self):
        """获取软件信息"""
        software = {
            "packages": {},
            "services": self.run_command("systemctl list-unit-files --type=service").split('\n') if self.run_command("which systemctl") else [],
            "python_packages": self.run_command("pip list --format=json").split('\n') if self.run_command("which pip") else []
        }
        
        # Debian/Ubuntu
        dpkg = self.run_command("dpkg --list | wc -l")
        if dpkg:
            software["packages"]["dpkg"] = f"{int(dpkg) - 5} packages"
        
        # RHEL/CentOS
        rpm = self.run_command("rpm -qa | wc -l")
        if rpm:
            software["packages"]["rpm"] = f"{rpm} packages"
        
        # Snap
        snap = self.run_command("snap list | wc -l")
        if snap:
            software["packages"]["snap"] = f"{int(snap) - 1} packages"
        
        # Flatpak
        flatpak = self.run_command("flatpak list | wc -l")
        if flatpak:
            software["packages"]["flatpak"] = f"{int(flatpak) - 1} packages"
        
        pc_info_dic['app_info'] = software

    def get_driver_info(self):
        """获取驱动信息"""
        pc_info_dic['driver_info'] = {
            "loaded_modules": self.run_command("lsmod").split('\n'),
            "pci_devices": self.run_command("lspci -k").split('\n'),
            "usb_devices": self.run_command("lsusb").split('\n')
        }

    # def get_security_info() -> dict[str, Union[List[str], dict[str, str]]]:
    #     """获取安全信息"""
    #     return {
    #         "users": run_command("getent passwd | cut -d: -f1").split('\n'),
    #         "sudoers": get_file_content('/etc/sudoers'),
    #         "ssh_keys": run_command("find /etc/ssh -name '*.pub' -exec cat {} \\;").split('\n'),
    #         "firewall": {
    #             "ufw": run_command("ufw status").split('\n') if run_command("which ufw") else [],
    #             "iptables": run_command("iptables -L -n").split('\n') if run_command("which iptables") else []
    #         }
    #     }
    def collect_system_info(self):
        """收集所有系统信息"""
        return {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "PC_Info Version": tool_ver,
                "PC_Info Release": release_date
            },
            "system_info": self.get_system_info(),
            "os_info": self.get_os_info(),
            "bios_info": self.get_bios_info(),
            "cpu_info": self.get_cpu_info(),
            "gpu_info": self.get_video_info(),
            "memory_info": self.get_ram_info(),
            "storage_info": self.get_disk_info(),
            "audio_info": self.get_audio_info(),
            "display_info": self.get_panel_info(),
            # "network": get_network_info(),
            "battery_info": self.get_battery_info(),
            "software_info": self.get_app_info(),
            "drivers_info": self.get_driver_info(),
            # "security": get_security_info()
        }
    
    def save_to_json(self, data, filename: str = "pc_info.json"):
        """保存数据到JSON文件"""
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"System information saved to {os.path.abspath(filename)}")

def generate_pc_all_info(os_type):
    if os_type == 'Windows':
        obj = Win32Wmi()
    elif os_type == 'Linux':
        obj = LinuxOS()
    obj.get_system_info()
    obj.get_os_info()
    obj.get_bios_info()
    obj.get_ram_info()
    obj.get_cpu_info()
    obj.get_disk_info()
    obj.get_battery_info()
    obj.get_audio_info()
    obj.get_panel_info()
    obj.get_camera_info()
    obj.get_touchpad_info()
    obj.get_keyboard_info()
    if os_type == 'Windows':
        obj.get_biometric_info()
    obj.get_network_info()
    obj.get_app_info()
    obj.get_driver_info()

def main():
    try:
        args = parsAttibute()
        if args.version:
            print(f'{tool_name} {tool_ver} {release_date}')
            sys.exit(0)
        if args.list:
            print(f'Get attribute list:')
            for i in pc_info_items:
                print(f'{i}')
            print('\nExample:\n'
                  'Get one attribute: PC_Info -get driver'
                    '\nGet more than one attribute: PC_Info -get "cpu ram disk"')
            sys.exit(0)
        item_list = args.get
        print(f'Attribute info: {item_list}')
        os_type = get_os_type()
        print(f'os type: {os_type}')
        if item_list == None:
            generate_pc_all_info(os_type)
        else:
            item_list = item_list.split(" ")
            if os_type == 'Windows':
                obj = Win32Wmi()
            elif os_type == 'Linux':
                obj = LinuxOS()
            else:
                print(f'Not support OS: {os_type}')
                sys.exit(0)
            for attr in item_list:
                if attr in ('', None):
                    continue
                if attr not in pc_info_items:
                    print(f'Your input: "{attr}" is a not support attribute,\
                           please use -h for view all attibute!')
                    continue
                if attr == 'biometric' and os_type == 'Linux':
                    print('Linux os not have biometric args, skip this step')
                    continue
                getattr(obj, "get_" + attr.lower() + "_info")()
        write_to_json()
        print('All steps are completed')
        os.system('pause')
    except Exception as ex:
        print(ex)
        print('Execute occur error!')

if __name__=='__main__':
    main()
    