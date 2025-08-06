import paramiko
import time
import re
import sys
import os
import pyautogui
import pexpect





# 设置控制台编码为UTF-8，解决Windows乱码问题
if sys.platform == "win32":
    os.system("chcp 65001 >nul 2>&1")


def ssh_run(host, username, password, cmd):
    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(hostname=host, port=22,username=username, password=password, timeout=10,look_for_keys=False)
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
    print("确保 APT 非交互模式",out)
    out = send_and_wait("sudo DEBIAN_FRONTEND=noninteractive apt-get update", pattern=r"Done", wait=1)
    print('-'*50)
    print("安装包",out)
    out = send_and_wait("sudo DEBIAN_FRONTEND=noninteractive apt-get -y install iptables-persistent", pattern=r"root@vultr", wait=1)
    print('-'*50)
    print("设置成功\n",out)
    print("输入脚本链接开始创建 bash <(wget -qO- https://raw.githubusercontent.com/yonggekkk/sing-box-yg/main/sb.sh)")
    #out = send_and_wait("bash <(wget -qO- https://raw.githubusercontent.com/yonggekkk/sing-box-yg/main/sb.sh)", pattern=r"<No>", wait=1)
    #print(out,"\r检测到弹窗 自动确认")
    # 模拟按下和释放回车键
    #pyautogui.press('enter')
    
    

    out = send_and_wait("bash <(wget -qO- https://raw.githubusercontent.com/yonggekkk/sing-box-yg/main/sb.sh)", pattern=r"请输入数字【0-16】", wait=1)
    print('-'*50)
    print("创建成功，输入数字1 安装sing-box", out)
    out = send_and_wait("1", pattern=r"请选择【1-2】", wait=1)
    print('-'*50)
    print("选择防火墙，输入数字1", out)
    out = send_and_wait("1", pattern=r"请选择【1-2】", wait=1)
    print('-'*50)
    print("选择内核，输入数字1", out)
    out = send_and_wait("1", pattern=r"请选择【1-2】", wait=1)
    print('-'*50)
    print("选择自签证书，输入数字1", out)
    out = send_and_wait("1", pattern=r"请输入【1-2】", wait=1)
    print('-'*50)
    print("选择协议端口，输入数字1", out)
    out = send_and_wait("1", pattern=r"Hysteria2/Tuic5自定义V2rayN配置、Clash-Meta/Sing-box客户端配置及私有订阅链接，请选择9查看", wait=1)
    print(out)

    chan.close()
    ssh.close()
print(sys.argv[1],"\n",sys.argv[2])
start=input("是否开始执行脚本（y/n）？")
if start == "Y" or start == "y":
    
    ssh_run(sys.argv[1], 'root', sys.argv[2], 'sb')





