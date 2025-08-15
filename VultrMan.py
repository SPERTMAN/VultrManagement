#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
执行 vultr-cli instance list 命令并打印输出结果
"""

import subprocess
import re
import sys
import paramiko
import time
import os
import pyautogui
import pexpect
import math
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime
import signal
from rich.console import Console
from rich.panel import Panel
from pyfiglet import Figlet
from rich.text import Text
from datetime import datetime
import sqlite3

# 设置控制台编码为UTF-8，解决Windows乱码问题
if sys.platform == "win32":
    os.system("chcp 65001 >nul 2>&1")

def Logs():
    # 创建日志目录
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # 日志文件路径（按日期命名）
    log_path = os.path.join(log_dir, datetime.now().strftime("%Y-%m-%d") + ".log")

    # 设置 logger
    logger = logging.getLogger("daily_logger")
    logger.setLevel(logging.DEBUG)

    # 创建按时间切分的处理器（每天创建一个）
    handler = TimedRotatingFileHandler(log_path, when="midnight", interval=1, backupCount=7, encoding='utf-8')
    handler.suffix = "%Y-%m-%d.log"

    # 日志格式
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    # 添加处理器
    logger.addHandler(handler)
    logger.propagate = False  # 防止重复输出
    return logger

def parse_instance_ids(output):
    """从 vultr-cli 输出中解析实例ID"""
    instance_ids = []

    # 按行分割输出
    lines = output.strip().split('\n')

    # 查找数据行（跳过标题行和分隔符）
    for line in lines:
        # 匹配UUID格式的实例ID（8-4-4-4-12格式）
        uuid_pattern = r'^([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})'
        match = re.match(uuid_pattern, line.strip())

        if match:
            instance_id = match.group(1)
            instance_ids.append(instance_id)
    
    if len(instance_ids) > 0:
        return instance_ids[0]
    else:
        return None


def parse_ip_pwd(output):
    """从 vultr-cli 输出中ip pwd"""
    instance_ids = []

    ip_address = re.search(r"MAIN IP\s+([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)", output)
    password = re.search(r"PASSWORD\s+(\S+)", output)
    return ip_address.group(1),password.group(1)
   
def Log_info(Type):
    """
    写入创建实例的时间以方便计算消费
    """

    

def run_vultr_instance_list(command,is_instance):
    """执行 vultr-cli instance list 命令"""
    try:
        #print("查看ID 正在执行: vultr-cli instance list")
        # 执行命令
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30
        )

        # 打印输出
        if result.returncode == 0:
            
            #print(result.stdout)
            if is_instance==0:
                # 解析实例ID
                instance_ids = parse_instance_ids(result.stdout)
                
                # 返回实例ID列表
                return instance_ids
            elif is_instance==2:
                print(result.stdout)
                return True
            elif is_instance==3:
                return parse_ip_pwd(result.stdout)
            elif is_instance==4:
                return re.search(r"POWER STATUS\s+(\S+)", result.stdout).group(1)
            else:
                return True

        else:
            print(f"命令执行失败，返回码: {result.returncode}")
            if result.stderr:
                print("错误信息:")
                print(result.stderr)
            return None
            

    except FileNotFoundError:
        print("错误: 未找到 vultr-cli 命令")
        print("请确保已安装 vultr-cli 并添加到 PATH 环境变量中")
        return False
    except subprocess.TimeoutExpired:
        print("错误: 命令执行超时")
        return False
    except Exception as e:
        print(f"错误: {e}")
        return False

def ssh_run(host, username, password, cmd):
    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(hostname=host, port=22,username=username, password=password, timeout=20,look_for_keys=False)
    except Exception as e:
        print(f"连接失败{e}")
        return
    chan = ssh.invoke_shell(term='vt100', width=120, height=40)
    time.sleep(0.5)
    chan.recv(1024)  # 清掉欢迎 banner

    def send_and_wait(cmd, pattern=None, wait=3):
        chan.send(cmd + "\n")
        buff = ""
        t0 = time.time()
        while True:
            if chan.recv_ready():
                chunk = chan.recv(4096).decode('utf‑8', errors='ignore')
                buff += chunk
            if pattern and re.search(pattern, buff) or re.search("command not found", buff):
                return buff
            if (time.time() - t0) > 60:
                raise TimeoutError(f"指定 pattern `{pattern}` 没有出现在输出中：\n{buff!r}")
            time.sleep(0.1)
    cmd=[
        # 设置 debconf 回答：自动保存 IPv4、IPv6 规则
        "echo iptables-persistent iptables-persistent/autosave_v4 boolean true | sudo debconf-set-selections",
        # 确保 APT 非交互模式
        "sudo DEBIAN_FRONTEND=noninteractive apt-get update",
        # 安装包
        "sudo DEBIAN_FRONTEND=noninteractive apt-get -y install iptables-persistent",
    ]
    print("连接成功，自动配置ipv4 避免弹窗")
    out = send_and_wait("echo iptables-persistent iptables-persistent/autosave_v4 boolean true | sudo debconf-set-selections", pattern=r"set-selections", wait=1)
    print('-'*50)
    print("确保 APT 非交互模式")
    out = send_and_wait("sudo DEBIAN_FRONTEND=noninteractive apt-get update", pattern=r"Done", wait=1)
    print('-'*50)
    print("安装包")
    out = send_and_wait("sudo DEBIAN_FRONTEND=noninteractive apt-get -y install iptables-persistent", pattern=r"root@vultr", wait=1)
    print('-'*50)
    print("设置成功\n")
    print("输入脚本链接开始创建 bash <(wget -qO- https://raw.githubusercontent.com/yonggekkk/sing-box-yg/main/sb.sh)")
    
    out = send_and_wait("bash <(wget -qO- https://raw.githubusercontent.com/yonggekkk/sing-box-yg/main/sb.sh)", pattern=r"请输入数字【0-16】", wait=1)
    print('-'*50)
    print("创建成功，输入数字1 安装sing-box")
    out = send_and_wait("1", pattern=r"请选择【1-2】", wait=1)
    print('-'*50)
    print("选择防火墙，输入数字1")
    out = send_and_wait("1", pattern=r"请选择【1-2】", wait=1)
    print('-'*50)
    print("选择内核，输入数字1")
    out = send_and_wait("1", pattern=r"请选择【1-2】", wait=1)
    print('-'*50)
    print("选择自签证书，输入数字1")
    out = send_and_wait("1", pattern=r"请输入【1-2】", wait=1)
    print('-'*50)
    print("选择协议端口，输入数字1")
    out = send_and_wait("1", pattern=r"Hysteria2/Tuic5自定义V2rayN配置、Clash-Meta/Sing-box客户端配置及私有订阅链接，请选择9查看", wait=1)
    print(out)

    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    out=ansi_escape.sub('',out)
    # 使用正则匹配 dmxlc3M6Ly9 开头的订阅链接
    match = re.search(r"(dmxlc3M6Ly[^\s]+)", out)
    
    
    if match:
        subscription_link = match.group(1)
        print("解析到的订阅链接：")
        print(subscription_link)
    else:
        print("未找到订阅链接")
        return

    import base64
    # 你的 Base64 字符串
    base64_string =subscription_link

    # 解码 Base64
    decoded_bytes = base64.b64decode(base64_string)
    decoded_string = decoded_bytes.decode('utf-8')

    Sqlite_parse_link(decoded_string)

    chan.close()
    ssh.close()
    time.sleep(3)
    open_soft(r"E:\v2rayN-windows-64-desktop\v2rayN-windows-64\v2rayN.exe")



def get_log_timestamps(log_file_path):
    """
    从日志文件中提取所有时间戳（datetime 对象）。
    """
    timestamps = []
    with open(log_file_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                # 解析日志时间，默认格式为：2025-08-06 12:00:01,123
                time_str = line.split(' - ')[0]
                dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S,%f")
                timestamps.append(dt)
            except Exception as e:
                continue  # 忽略非标准格式行
    return timestamps

def get_time_diff_between_logs(log_file_path):
    """
    返回日志文件中两条日志的时间差（以秒为单位）。
    """
    timestamps = get_log_timestamps(log_file_path)
    if 2 > len(timestamps) :
        raise IndexError("日志索引超出范围")
    diff = math.ceil(abs((timestamps[len(timestamps)-1] - timestamps[len(timestamps)-2]).total_seconds())/3600)
    diff=1 if diff==0 else diff
    return diff


def print_big_banner(text="Vultr", color="cyan"):
    # 生成 ASCII 大字
    console = Console()
    figlet = Figlet(font='slant')  # 可选字体如 'banner', 'standard', 'doom'
    ascii_art = figlet.renderText(text)

    # 使用 rich 加颜色和边框
    styled_text = Text(ascii_art, style=color,justify="center")
    panel = Panel(styled_text, border_style=color, title="vultr-cli 管理工具")
    console.print(panel)

def Check_other_Vpn(process_name):
    import psutil
    # 遍历所有进程
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            # 如果进程名称匹配 in：检查左边的字符串是否包含右边的字符串
            if process_name.lower() in proc.info['name'].lower():
                print(f"Found process {proc.info['name']} with PID {proc.info['pid']}")
                proc.terminate()  # 尝试关闭进程
                print(f"Process {proc.info['name']} terminated.")
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass  # 忽略无效的进程

    print(f"Process {process_name} not found.")
    return False

def open_soft(exe):
    import subprocess

    # 打开记事本
    subprocess.Popen([exe])




def Sqlite_config_del():
   
    conn = sqlite3.connect(sqlite_path)
    cursor = conn.cursor()
    # 执行查询：从sqlite_master表获取所有表的名称
    #cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    # 输出所有表名
    #for table in tables:
        #print(table[0])
    #删除之前的记录
    cursor.execute("DELETE  FROM  ProfileItem")
    # 提交更改
    conn.commit()
    # 获取查询结果
    cursor.execute("SELECT * FROM ProfileItem")

    tables = cursor.fetchall()
    if len(tables)==0:
        print("删除 节点配置 成功")

    conn.close()

def Sqlite_parse_link(url):
    url_list=url.splitlines()
    conn = sqlite3.connect(sqlite_path)
    # 默认脚本id)
    cursor = conn.cursor()
    pattern = r"(\w+)://([\w-]+)@([\d.]+):(\d+)\?security=([^&]+)&alpn=([^&]+)&insecure=([^&]+)&sni=([^#]+)"

    for url in url_list:
        match = re.search(pattern, url)

        if match:
            proto, uuid, host, port, security, alpn, insecure, sni = match.groups()

            command= f"""
            INSERT INTO ProfileItem (
                                        MuxEnabled,
                                        Extra,
                                        Mldsa65Verify,
                                        SpiderX,
                                        ShortId,
                                        PublicKey,
                                        DisplayLog,
                                        Fingerprint,
                                        PreSocksPort,
                                        CoreType,
                                        Alpn,
                                        Sni,
                                        Flow,
                                        IsSub,
                                        Subid,
                                        AllowInsecure,
                                        StreamSecurity,
                                        Path,
                                        RequestHost,
                                        HeaderType,
                                        Remarks,
                                        Network,
                                        Security,
                                        AlterId,
                                        Id,
                                        Ports,
                                        Port,
                                        Address,
                                        ConfigVersion,
                                        ConfigType,
                                        IndexId
                                    )
                                    VALUES (
                                        NULL,
                                        NULL,
                                        '',
                                        '',
                                        '',
                                        '',
                                        1,
                                        '',
                                        NULL,
                                        24,
                                        'h3',
                                        '{sni}',
                                        '',
                                        0,
                                        NULL,
                                        'true',
                                        '{security}',
                                        '',
                                        '',
                                        'none',
                                        'hy2-vultr',
                                        '',
                                        '',
                                        0,
                                        '{uuid}',
                                        '',
                                        {port},
                                        '{host}',
                                        2,
                                        7,
                                        1
                                    );

            """

            cursor.execute(command)
            conn.commit()

            cursor.execute("SELECT * FROM ProfileItem")
            print("加入成功")
    conn.close()




def main():
    """主函数"""
    global sqlite_path
    instance_para_id = ""
    snapshot_para_id = ""
    
    delete_enable=False
    New_enable=True

    # 生成实例参数
    set_instance_para = ""
    
    # 默认东京
    Area = "nrt"
    
    # 默认PLAN
    Plan = "vc2-1c-1gb"

    # 默认os
    os_id = "2136"
    #db path
    sqlite_path=r"E:\v2rayN-windows-64-desktop\v2rayN-windows-64\guiConfigs\guiNDB.db"
    # 默认脚本id
    scriptid_id="75e09113-bc1e-4d0d-902c-92ca164f8c34"
    ip_address=""
    pwd=""
    

    Get_instance_id_cmd = ["vultr-cli", "instance", "list"]
    Get_snapshot_id_cmd = ["vultr-cli", "snapshot", "list"]
   
    
    

    #标题
    print_big_banner("Vultr", color="bright_magenta")

    #加载日志
    LogVar=Logs()

    #关闭连接影响的相关软件
    Check_other_Vpn("v2rayN.exe")
    Check_other_Vpn("clash-verge.exe")

    
    #diff_seconds=2
    #print(f"具体使用时间为 \033[1m{diff_seconds}\033[0m 小时")
    #print(f"预计费用 \033[1m{diff_seconds*0.01 }\033[0m 美元")
    #print(f"结合人民币 \033[1m{diff_seconds*0.01*7.18 }\033[0m 元")
    

    #print("连接实例...")
    
    #snapshot_para_id = run_vultr_instance_list(Get_snapshot_id_cmd,0)

     # 检查实例ID
    #if instance_para_id is None:
    #    delete_enable = False
    #else:
    #   delete_enable = True
     #   delete_instance.append(instance_para_id)
     #   instance_info.append(instance_para_id)  
    #print("未找到实例ID不能使用删除" if instance_para_id is None else f"解析到的实例ID:{instance_para_id}")
    print("-" * 50)
    # 检查快照ID
    #New_enable = False if snapshot_para_id is None else True
    #print("未找到快照ID不能使用新建" if snapshot_para_id is None else f"解析到的实例ID:{snapshot_para_id}")
    #print("-" * 50)
    

    while True:
        print("-" * 50)
        Command = input("请输入命令（删除实例=1 新建实例=2 查看实例信息=3 建立节点=4 退出=10）：")
        if Command == "1":
            
            instance_para_id = run_vultr_instance_list(Get_instance_id_cmd,0)
            if instance_para_id == None:
                print("\n未找到实例ID不能使用删除")
                return
            
            print("\n开始执行删除实例")
            delete_instance = ["vultr-cli", "instance", "delete", instance_para_id]
            if run_vultr_instance_list(delete_instance,1) :
                LogVar.info(f"删除成功 id {instance_para_id}")
                time.sleep(2)
                today_log = os.path.join("logs", datetime.now().strftime("%Y-%m-%d") + ".log")
                diff_seconds = get_time_diff_between_logs(today_log)
                print(f"具体使用时间为 \033[1m{diff_seconds}\033[0m 小时")
                print(f"预计费用 \033[1m{diff_seconds*0.01 }\033[0m 美元")
                print(f"结合人民币 \033[1m{diff_seconds*0.01*7.18 }\033[0m 元")
                print("删除成功")
            else:
                print("删除失败")
       
        elif Command == "2":
            instance_para_id = run_vultr_instance_list(Get_instance_id_cmd,0)
            if  instance_para_id!=None:
                print(f"\n存在实例{instance_para_id}（目前存在实例不能创建）")
                
            
            print("\n开始执行新建实例")
            set_instance_para=f"--region {Area} --plan {Plan} --os {os_id} --label \"NewInstance\" --script-id {scriptid_id}"
            #print(set_instance_para)
            new_instance = ["vultr-cli",         # 可执行程序
                            "instance", "create",
                            "--region",   Area,
                            "--plan",     Plan,
                            "--os", os_id,
                            "--label",   "NewInstance",
                            "--script-id",   scriptid_id
                            ]
            
            if run_vultr_instance_list(new_instance,1) :
                LogVar.info(f"创建成功")
                print("创建成功")
            else:
                print("创建失败")
                
        elif Command =="3":
            instance_para_id = run_vultr_instance_list(Get_instance_id_cmd,0)
            if instance_para_id == None:
                print("\n未找到实例ID不能使用查看")
                
            print("\n开始执行查看实例信息")
            instance_info = ["vultr-cli", "instance", "get",instance_para_id]
            if run_vultr_instance_list(instance_info,2) :
                print("查看成功")
            else:
                print("查看失败")
        elif Command=="4":
            Sqlite_config_del()
            start=input("是否开始执行脚本（y/n）？")
            if start == "Y" or start == "y":
                #查询ip和密码
                #print("密码查询未有解决办法")
                instance_para_id = run_vultr_instance_list(Get_instance_id_cmd,0)
                if instance_para_id == None:
                    print("\n未找到实例ID不能创建节点")
                    continue
                time.sleep(10)
                print("开始等待实例激活")
                start_ssh=False
                while start_ssh==False:
                    time.sleep(2) 
                    power_status=run_vultr_instance_list(["vultr-cli", "instance", "get",instance_para_id],4)
                    print(f"\n状态：{power_status}")
                    if power_status=="running":
                        print("开机完成")
                        start_ssh=True
                        time.sleep(5)
                ip,pwd=run_vultr_instance_list(["vultr-cli", "instance", "get",instance_para_id],3)

                if pwd=='UNAVAILABLE':
                    print("\n密码为：UNAVAILABLE，请自行去官网登录查看")
                    pwd=input("手动查看密码（取消 ：n）")
                    if pwd=="n"or pwd=="N":
                        continue
                print(f"\n解析成功，ip：{ip} 密码：{pwd}")
                #return
                time.sleep(5)
                ssh_run(ip, 'root', pwd, 'sb')
                
                
        elif Command=="10":
            # Windows 下获取父进程（通常是 cmd.exe）
            ppid = os.getppid()
            os.kill(ppid, signal.SIGTERM)  # 或者 SIGKILL
            return
        else:
            print("未知指令")

       


if __name__ == "__main__":
    main()