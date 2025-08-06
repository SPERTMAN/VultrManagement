# Vultr CLI 实例管理工具

这是一个简单的 Python 脚本，用于执行 `vultr-cli ` 命令用来方便管理vultr的VPS来实现节省钱。

配合**create_node.py**（目前vultr使用ssh建立的实例获取不了密码，所以任需要手动进入vultr页面或者密码，主要建立ssh连接自动拉取脚本创建节点）使用。

## 功能特性

- 执行 `vultr-cli` 命令
- 删除实例（删除后不扣除费用，达到省钱目的）
- 创建实例（VPS）

## 使用方法

### 方法一：直接运行 Python 脚本

```bash
python VultrMan.py
```

### 方法二：使用批处理文件（Windows）

```cmd
# 双击运行或在 CMD 中执行
run_vultr_list.bat
```

## 前置要求

1. **Python 3.6+**: 确保系统已安装 Python 3.6 或更高版本
2. **vultr-cli**: 需要安装并配置 Vultr CLI 工具

### 安装 vultr-cli

1. 从 [Vultr CLI GitHub](https://github.com/vultr/vultr-cli) 下载对应系统的版本
2. 将可执行文件放到 PATH 环境变量中
3. 配置 API 密钥：
   ```bash
   setx VULTR_API_KEY "123456" -m
   ```

### **使用create_node.py**

使用创建脚本：[github](https://github.com/yonggekkk/sing-box-yg)

这里依然有方法，就是通过创建脚本先设立密码，具体参考：[vultr](https://clh021.github.io/vultr/)

1. 进入**vultr**查看密码

2. 用本文打开**run_create_node.bat**将**IP**和**密码**填入

   > python create_node.py  IP 密码

3. 保存运行**run_create_node.bat**

   

## 错误处理

脚本会自动处理以下情况：
- vultr-cli 未安装或不在 PATH 中
- API 认证失败
- 网络连接问题
- 命令执行超时

1. **"vultr-cli 不可用"**: 确保已安装 vultr-cli 并在 PATH 中
2. **"命令执行失败"**: 检查 API 密钥配置是否正确
3. **"命令执行超时"**: 检查网络连接
