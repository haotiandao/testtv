import os
import re
import requests
import socket

print("=== 脚本开始运行 ===")

# 配置区
COUNTER_FILE = "计数.txt"
IP_DIR = "ip"
RTP_DIR = "rtp"

def get_run_count():
    if os.path.exists(COUNTER_FILE):
        try:
            return int(open(COUNTER_FILE, "r", encoding="utf-8").read().strip() or "0")
        except Exception:
            return 0
    return 0

def save_run_count(count):
    try:
        with open(COUNTER_FILE, "w", encoding="utf-8") as f:
            f.write(str(count))
    except Exception as e:
        print(f"⚠️ 写计数文件失败：{e}")

# 测试第一阶段
print("📁 检查 ip_urls.txt 是否存在...")
if os.path.exists("ip_urls.txt"):
    print("✅ ip_urls.txt 存在")
    with open("ip_urls.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()
        print(f"📊 文件中有 {len(lines)} 行")
        for i, line in enumerate(lines[:5]):
            print(f"  {i+1}: {line.strip()}")
else:
    print("❌ ip_urls.txt 不存在")

print("=== 脚本测试完成 ===")
