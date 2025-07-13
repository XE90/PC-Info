# PC_Info
一个抓取电脑(Windows,Linux系统)各种信息的工具, 并将信息生成到一个JSON文档中。
具有简洁、轻量级、便于与其它工具进行数据交互等特点
支持在命令行中执行带参数操作
Author: Gavin.Xie
Version: 1.7.0

## PC_Info 抓取的电脑信息如下
包括版本、厂商、固件、VID、PID、HWID、发布日期等。
部件涉及到处理器、内存、BIOS、OS、System、GPU、
Storage、Driver、Battery、Panel、Camera、Biometric、
TouchPad、Keyboard、Audio、Network Card、Software、
Driver等。

## 生成可执行文件方式
pyisntaller --onefile PC_Info_v1.7.0.py

## 文件结构
```
├── PC_Info_v1.7.0.py           # 代码脚本
```
## 如有问题，请联系
x3012378557@outlook.com

## Version
2025.07.12 Gavin.Xie v1.7.0, Add collect PC info for Linux system.
2025.07.07 Gavin.Xie v1.6.0, Add Battery Health and Battery cycle count to Battery_Info section.
2025.07.01 Gavin.Xie v1.5.0, Modify codes in systemInfo/batteryInfo/AppInfo section.
2025.05.01 Gavin.Xie v1.4.0, Modify codes in systemInfo/batteryInfo section.
2025.04.10 Gavin.Xie v1.3.0, Fix some issue when not have apps & products & device.
2025.03.28 Gavin.Xie v1.2.2, Add driver date info to driver section. Modify some codes.
2024.10.16 Gavin.Xie v1.2.1, Add tool version info to json file; Modify OS version display format.
2024.07.25 Gavin.Xie v1.2.1 Add Memory Vendor and more info to Memory section.
2023.1 Gavin.Xie v0.0.1 Add CPU,BIOS,RAM,System section.
