def first_stage():
    os.makedirs(IP_DIR, exist_ok=True)
    all_ips = set()

    # ========== 优先从本地 ip_urls.txt 读取IP ==========
    if os.path.exists("ip_urls.txt"):
        print("📁 从本地 ip_urls.txt 读取IP...")
        try:
            with open("ip_urls.txt", "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    # 跳过空行和注释行
                    if not line or line.startswith("#"):
                        continue
                    # 处理 http://IP:端口 格式（您的文件是这个格式）
                    if line.startswith("http://"):
                        # 提取 IP:端口 部分
                        ip_part = line.replace("http://", "").split("/")[0]
                        all_ips.add(ip_part)
                    else:
                        # 直接是 IP:端口 格式
                        all_ips.add(line)
            print(f"✅ 从本地文件读取到 {len(all_ips)} 个IP")
        except Exception as e:
            print(f"⚠️ 读取本地文件失败：{e}")
    # ===================================================

    # 如果本地没有IP，再尝试从FOFA爬取（保留原逻辑作为备选）
    if not all_ips:
        for url, filename in FOFA_URLS.items():
            print(f"📡 正在爬取 {filename} ...")
            try:
                r = requests.get(url, headers=HEADERS, timeout=15)
                urls_all = re.findall(r'<a href="http://(.*?)"', r.text)
                all_ips.update(u.strip() for u in urls_all if u.strip())
            except Exception as e:
                print(f"❌ 爬取失败：{e}")
            time.sleep(3)

    if not all_ips:
        print("⚠️ 未获取到任何IP")
        return 0

    # ========== 以下代码完全不变 ==========
    province_isp_dict = {}

    for ip_port in all_ips:
        try:
            host = ip_port.split(":")[0]

            is_ip = re.match(r"^\d{1,3}(\.\d{1,3}){3}$", host)

            if not is_ip:
                try:
                    resolved_ip = socket.gethostbyname(host)
                    print(f"🌐 域名解析成功: {host} → {resolved_ip}")
                    ip = resolved_ip
                except Exception:
                    print(f"❌ 域名解析失败，跳过：{ip_port}")
                    continue
            else:
                ip = host

            res = requests.get(f"http://ip-api.com/json/{ip}?lang=zh-CN", timeout=10)
            data = res.json()

            province = data.get("regionName", "未知")
            isp = get_isp_from_api(data)

            if isp == "未知":
                isp = get_isp_by_regex(ip)

            if isp == "未知":
                print(f"⚠️ 无法判断运营商，跳过：{ip_port}")
                continue

            fname = f"{province}{isp}.txt"
            province_isp_dict.setdefault(fname, set()).add(ip_port)

        except Exception as e:
            print(f"⚠️ 解析 {ip_port} 出错：{e}")
            continue

    count = get_run_count() + 1
    save_run_count(count)

    for filename, ip_set in province_isp_dict.items():
        path = os.path.join(IP_DIR, filename)
        try:
            with open(path, "a", encoding="utf-8") as f:
                for ip_port in sorted(ip_set):
                    f.write(ip_port + "\n")
            print(f"✅ {path} 已追加写入 {len(ip_set)} 个 IP")
        except Exception as e:
            print(f"❌ 写入 {path} 失败：{e}")

    print(f"✅ 第一阶段完成，当前轮次：{count}")
    return count
