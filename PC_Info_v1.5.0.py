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

print('*****************************************************************')
print('*                     Tool: PC Info                             *')
print('*                  Version: v1.5.0                              *')
print('*             Release Date: 2025.07.01                          *')
print('*                   Author: Gavin.Xie                           *')
print('*****************************************************************')
print('\n')

'''
2025.07.01 Gavin.Xie v1.5.0, Modify codes in systemInfo/batteryInfo/AppInfo section.
2025.05.01 Gavin.Xie v1.4.0, Modify codes in systemInfo/batteryInfo section.
2025.04.10 Gavin.Xie v1.3.0, Fix some issue when not have apps & products & device.
2025.03.28 Gavin.Xie v1.2.2, Add driver date info to driver section. Modify some codes.
2024.10.16 Gavin.Xie v1.2.1, Add tool version info to json file; Modify OS version display format.
2024.07.25 Gavin.Xie v1.2.1 Add Memory Vendor and more info to Memory section.
2023.1 Gavin.Xie v0.0.1 Add CPU,BIOS,RAM,System section.
'''
tool_name = 'PC Info'
tool_ver = '1.5.0'
release_date = '2025.07.01'
author = 'Gavin.X'

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

    def system_info(self):
        print('Check system info ...')
        cmd = self.pw + 'ComputerSystem'
        get_system_cmd = ' '.join([cmd, '|','select Manufacturer,Model,Name,OEMStringArray,SystemType',
                                   '|', 'convertto-json', '"'])
        self.get_item_result('system', get_system_cmd)

    def os_info(self):
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

    def bios_info(self):
        print('Check BIOS info ...')
        cmd = self.pw + 'bios'
        get_bios_cmd = ' '.join([cmd, '|','select Manufacturer,SMBIOSBIOSVersion,SerialNumber',
                                   '|', 'convertto-json', '"'])
        self.get_item_result('bios', get_bios_cmd)

    def ram_info(self):
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

    def cpu_info(self):
        print('Check Processor info ...')
        cmd = self.pw + 'Processor'
        get_cpu_cmd = ' '.join([cmd, '|','select Caption,Name,Manufacturer, \
                        SocketDesignation,CurrentClockSpeed,MaxClockSpeed,CurrentVoltage, \
                        L2CacheSize', '|', 'convertto-json', '"'])
        self.get_item_result('CPU', get_cpu_cmd)

    def disk_info(self):
        print('Check Disk info ...')
        cmd = self.pw + 'diskdrive'
        get_disk_cmd = ' '.join([cmd, '|','select Model,Size,Firmwarerevision,InterfaceType,MediaType',
                                 '|', 'convertto-json', '"'])
        self.get_item_result('disk', get_disk_cmd)

    def battery_info(self):
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
            out1 = json.loads(out1)
            out.update(out1)
        print(f'{out}\n')
        pc_info_dic['Battery Info'] = out

    def video_info(self):
        print('Check Video info ...')
        cmd = self.pw + 'videocontroller'
        get_video_cmd = ' '.join([cmd, '|','select Name,DeviceID,CurrentHorizontalResolution, \
                        CurrentVerticalResolution,CurrentNumberOfColors,CurrentRefreshRate,MaxRefreshRate,\
                        MinRefreshRate,VideoModeDescription,VideoProcessor,AdapterCompatibility,AdapterDACType, \
                        DriverVersion','|', 'convertto-json', '"'])
        self.get_item_result('video', get_video_cmd)

    def audio_info(self):
        print('Check Audio info ...')
        cmd = self.pw + 'PnpEntity'
        get_audio_cmd = ' '.join([cmd, '|','where pnpclass -match "MEDIA"','|',
                                  'select Caption,Description,Status,ConfigManagerErrorCode,\
                        DeviceID,HardwareID,Manufacturer','|', 'convertto-json', '"'])
        self.get_item_result('audio', get_audio_cmd)

    def panel_info(self):
        print('Check Panel info ...')
        cmd = self.pw + 'DesktopMonitor'
        get_panel_cmd = ' '.join([cmd, '|','select DeviceID,Name,\
                        PixelsPerXLogicalInch,PixelsPerYLogicalInch,Status,ConfigManagerErrorCode,\
                        PNPDeviceID,MonitorManufacturer','|', 'convertto-json', '"'])
        self.get_item_result('panel', get_panel_cmd)

    def camera_info(self):
        print('Check Camera info ...')
        cmd = self.pw + 'PnpEntity'
        get_camera_cmd = ' '.join([cmd, '|','where pnpclass -match "camera"','|',
                                  'select Caption,Description,Status,ConfigManagerErrorCode,DeviceID, \
                        HardwareID,Manufacturer,Service', '|','convertto-json', '"'])
        self.get_item_result('camera', get_camera_cmd)
    
    def touchpad_info(self):
        print('Check Touchpad info ...')
        cmd = self.pw + 'PnpEntity'
        get_touchpad_cmd = ' '.join([cmd, '|','where pnpclass -match "HIDCLASS"','|',
                                  'select Caption,Description,Status,ConfigManagerErrorCode,\
                            DeviceID,HardwareID,Manufacturer', '|','convertto-json', '"'])
        self.get_item_result('touchpad', get_touchpad_cmd)

    def biometric_info(self):
        print('Check Biometric info ...')
        cmd = self.pw + 'PnpEntity'
        get_biometric_cmd = ' '.join([cmd, '|','where pnpclass -match "biometric"','|',
                                  'select Caption,Description,Status,ConfigManagerErrorCode,\
                            DeviceID,HardwareID,Manufacturer,Service', '|','convertto-json', '"'])
        self.get_item_result('biometric', get_biometric_cmd)

    def keyboard_info(self):
        print('Check Keyboard info ...')
        cmd = self.pw + 'PnpEntity'
        get_Keyboard_cmd = ' '.join([cmd, '|','where pnpclass -match "keyboard"','|',
                                  'select Caption,Description,Status,ConfigManagerErrorCode,\
                            DeviceID,HardwareID,Manufacturer,Service', '|','convertto-json', '"'])
        self.get_item_result('keyboard', get_Keyboard_cmd)

    def network_info(self):
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

    def app_info(self):
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

    def driver_info(self):
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

def generate_pc_all_info():
    obj = Win32Wmi()
    obj.system_info()
    obj.bios_info()
    obj.ram_info()
    obj.cpu_info()
    obj.disk_info()
    obj.battery_info()
    obj.audio_info()
    obj.panel_info()
    obj.camera_info()
    obj.touchpad_info()
    obj.biometric_info()
    obj.keyboard_info()
    obj.network_info()
    obj.app_info()
    obj.driver_info()

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
        if item_list == None:
            generate_pc_all_info()
        else:
            item_list = item_list.split(" ")
            obj = Win32Wmi()
            for attr in item_list:
                if attr in ('', None):
                    continue
                if attr not in pc_info_items:
                    print(f'Your input: "{attr}" is a not support attribute,\
                           please use -h for view all attibute!')
                    continue
                getattr(obj, attr.lower() + "_info")()
        write_to_json()
        print('All steps are completed')
        os.system('pause')
    except Exception as ex:
        print(ex)
        print('Execute occur error!')

if __name__=='__main__':
    main()
    
    
