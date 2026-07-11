import os
import re
import requests
import time
import concurrent.futures
import subprocess
import socket
from datetime import datetime, timezone, timedelta

# ===============================
# 配置区
FOFA_URLS = {
    "https://fofa.info/result?qbase64=InVkcHh5IiAmJiBjb3VudHJ5PSJDTiI%3D": "ip.txt",
}
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

COUNTER_FILE = "计数.txt"
IP_DIR = "ip"
RTP_DIR = "rtp"
ZUBO_FILE = "zubo.txt"
IPTV_FILE = "IPTV.txt"

# ===============================
# 分类与映射配置
CHANNEL_CATEGORIES = {
    "央视频道": [
        "CCTV1", "CCTV2", "CCTV3", "CCTV4", "CCTV4欧洲", "CCTV4美洲", "CCTV5", "CCTV5+", "CCTV6", "CCTV7",
        "CCTV8", "CCTV9", "CCTV10", "CCTV11", "CCTV12", "CCTV13", "CCTV14", "CCTV15", "CCTV16", "CCTV17", "CCTV4K", "CCTV8K",
        "兵器科技", "风云音乐", "风云足球", "风云剧场", "怀旧剧场", "第一剧场", "女性时尚", "世界地理", "央视台球", "高尔夫网球",
        "央视文化精品", "卫生健康", "电视指南", "中学生", "发现之旅", "书法频道", "国学频道", "环球奇观"
    ],
    "卫视频道": [
        "湖南卫视", "浙江卫视", "江苏卫视", "东方卫视", "深圳卫视", "北京卫视", "广东卫视", "广西卫视", "东南卫视", "海南卫视",
        "河北卫视", "河南卫视", "湖北卫视", "江西卫视", "四川卫视", "重庆卫视", "贵州卫视", "云南卫视", "天津卫视", "安徽卫视",
        "山东卫视", "辽宁卫视", "黑龙江卫视", "吉林卫视", "内蒙古卫视", "宁夏卫视", "山西卫视", "陕西卫视", "甘肃卫视", "青海卫视",
        "新疆卫视", "西藏卫视", "三沙卫视", "兵团卫视", "延边卫视", "安多卫视", "康巴卫视", "农林卫视", "山东教育卫视",
        "中国教育1台", "中国教育2台", "中国教育3台", "中国教育4台", "早期教育"
    ],
    "数字频道": [
        "CHC动作电影", "CHC家庭影院", "CHC影迷电影", "淘电影", "淘精彩", "淘剧场", "淘4K", "淘娱乐", "淘BABY", "淘萌宠", "重温经典",
        "星空卫视", "ChannelV", "凤凰卫视中文台", "凤凰卫视资讯台", "凤凰卫视香港台", "凤凰卫视电影台", "求索纪录", "求索科学",
        "求索生活", "求索动物", "纪实人文", "金鹰纪实", "纪实科教", "睛彩青少", "睛彩竞技", "睛彩篮球", "睛彩广场舞", "魅力足球", "五星体育",
        "劲爆体育", "快乐垂钓", "茶频道", "先锋乒羽", "天元围棋", "汽摩", "梨园频道", "文物宝库", "武术世界", "哒啵赛事", "哒啵电竞", "黑莓电影", "黑莓动画", 
        "乐游", "生活时尚", "都市剧场", "欢笑剧场", "游戏风云", "金色学堂", "动漫秀场", "新动漫", "卡酷少儿", "金鹰卡通", "优漫卡通", "哈哈炫动", "嘉佳卡通", 
        "中国交通", "中国天气", "华数4K", "华数星影", "华数动作影院", "华数喜剧影院", "华数家庭影院", "华数经典电影", "华数热播剧场", "华数碟战剧场",
        "华数军旅剧场", "华数城市剧场", "华数武侠剧场", "华数古装剧场", "华数魅力时尚", "华数少儿动画", "华数动画"
    ],
}

# ===== 映射（别名 -> 标准名） =====
CHANNEL_MAPPING = {
    "CCTV1": ["CCTV-1", "CCTV-1 HD", "CCTV1 HD", "CCTV-1综合"],
    "CCTV2": ["CCTV-2", "CCTV-2 HD", "CCTV2 HD", "CCTV-2财经"],
    "CCTV3": ["CCTV-3", "CCTV-3 HD", "CCTV3 HD", "CCTV-3综艺"],
    "CCTV4": ["CCTV-4", "CCTV-4 HD", "CCTV4 HD", "CCTV-4中文国际"],
    "CCTV4欧洲": ["CCTV-4欧洲", "CCTV-4欧洲", "CCTV4欧洲 HD", "CCTV-4 欧洲", "CCTV-4中文国际欧洲", "CCTV4中文欧洲"],
    "CCTV4美洲": ["CCTV-4美洲", "CCTV-4北美", "CCTV4美洲 HD", "CCTV-4 美洲", "CCTV-4中文国际美洲", "CCTV4中文美洲"],
    "CCTV5": ["CCTV-5", "CCTV-5 HD", "CCTV5 HD", "CCTV-5体育"],
    "CCTV5+": ["CCTV-5+", "CCTV-5+ HD", "CCTV5+ HD", "CCTV-5+体育赛事"],
    "CCTV6": ["CCTV-6", "CCTV-6 HD", "CCTV6 HD", "CCTV-6电影"],
    "CCTV7": ["CCTV-7", "CCTV-7 HD", "CCTV7 HD", "CCTV-7国防军事"],
    "CCTV8": ["CCTV-8", "CCTV-8 HD", "CCTV8 HD", "CCTV-8电视剧"],
    "CCTV9": ["CCTV-9", "CCTV-9 HD", "CCTV9 HD", "CCTV-9纪录"],
    "CCTV10": ["CCTV-10", "CCTV-10 HD", "CCTV10 HD", "CCTV-10科教"],
    "CCTV11": ["CCTV-11", "CCTV-11 HD", "CCTV11 HD", "CCTV-11戏曲"],
    "CCTV12": ["CCTV-12", "CCTV-12 HD", "CCTV12 HD", "CCTV-12社会与法"],
    "CCTV13": ["CCTV-13", "CCTV-13 HD", "CCTV13 HD", "CCTV-13新闻"],
    "CCTV14": ["CCTV-14", "CCTV-14 HD", "CCTV14 HD", "CCTV-14少儿"],
    "CCTV15": ["CCTV-15", "CCTV-15 HD", "CCTV15 HD", "CCTV-15音乐"],
    "CCTV16": ["CCTV-16", "CCTV-16 HD", "CCTV-16 4K", "CCTV-16奥林匹克", "CCTV16 4K", "CCTV-16奥林匹克4K"],
    "CCTV17": ["CCTV-17", "CCTV-17 HD", "CCTV17 HD", "CCTV-17农业农村"],
    "CCTV4K": ["CCTV4K超高清", "CCTV-4K超高清", "CCTV-4K 超高清", "CCTV 4K"],
    "CCTV8K": ["CCTV8K超高清", "CCTV-8K超高清", "CCTV-8K 超高清", "CCTV 8K"],
    "兵器科技": ["CCTV-兵器科技", "CCTV兵器科技"],
    "风云音乐": ["CCTV-风云音乐", "CCTV风云音乐"],
    "第一剧场": ["CCTV-第一剧场", "CCTV第一剧场"],
    "风云足球": ["CCTV-风云足球", "CCTV风云足球"],
    "风云剧场": ["CCTV-风云剧场", "CCTV风云剧场"],
    "怀旧剧场": ["CCTV-怀旧剧场", "CCTV怀旧剧场"],
    "女性时尚": ["CCTV-女性时尚", "CCTV女性时尚"],
    "世界地理": ["CCTV-世界地理", "CCTV世界地理"],
    "央视台球": ["CCTV-央视台球", "CCTV央视台球"],
    "高尔夫网球": ["CCTV-高尔夫网球", "CCTV高尔夫网球", "CCTV央视高网", "CCTV-高尔夫·网球", "央视高网"],
    "央视文化精品": ["CCTV-央视文化精品", "CCTV央视文化精品", "CCTV文化精品", "CCTV-文化精品", "文化精品"],
    "卫生健康": ["CCTV-卫生健康", "CCTV卫生健康"],
    "电视指南": ["CCTV-电视指南", "CCTV电视指南"],
    "农林卫视": ["陕西农林卫视"],
    "三沙卫视": ["海南三沙卫视"],
    "兵团卫视": ["新疆兵团卫视"],
    "延边卫视": ["吉林延边卫视"],
    "安多卫视": ["青海安多卫视"],
    "康巴卫视": ["四川康巴卫视"],
    "山东教育卫视": ["山东教育"],
    "中国教育1台": ["CETV1", "中国教育一台", "中国教育1", "CETV-1 综合教育", "CETV-1"],
    "中国教育2台": ["CETV2", "中国教育二台", "中国教育2", "CETV-2 空中课堂", "CETV-2"],
    "中国教育3台": ["CETV3", "中国教育三台", "中国教育3", "CETV-3 教育服务", "CETV-3"],
    "中国教育4台": ["CETV4", "中国教育四台", "中国教育4", "CETV-4 职业教育", "CETV-4"],
    "早期教育": ["中国教育5台", "中国教育五台", "CETV早期教育", "华电早期教育", "CETV 早期教育"],
    "湖南卫视": ["湖南卫视4K"],
    "北京卫视": ["北京卫视4K"],
    "东方卫视": ["东方卫视4K"],
    "广东卫视": ["广东卫视4K"],
    "深圳卫视": ["深圳卫视4K"],
    "山东卫视": ["山东卫视4K"],
    "四川卫视": ["四川卫视4K"],
    "浙江卫视": ["浙江卫视4K"],
    "CHC影迷电影": ["CHC高清电影", "CHC-影迷电影", "影迷电影", "chc高清电影"],
    "淘电影": ["IPTV淘电影", "北京IPTV淘电影", "北京淘电影"],
    "淘精彩": ["IPTV淘精彩", "北京IPTV淘精彩", "北京淘精彩"],
    "淘剧场": ["IPTV淘剧场", "北京IPTV淘剧场", "北京淘剧场"],
    "淘4K": ["IPTV淘4K", "北京IPTV4K超清", "北京淘4K", "淘4K", "淘 4K"],
    "淘娱乐": ["IPTV淘娱乐", "北京IPTV淘娱乐", "北京淘娱乐"],
    "淘BABY": ["IPTV淘BABY", "北京IPTV淘BABY", "北京淘BABY", "IPTV淘baby", "北京IPTV淘baby", "北京淘baby"],
    "淘萌宠": ["IPTV淘萌宠", "北京IPTV萌宠TV", "北京淘萌宠"],
    "魅力足球": ["上海魅力足球"],
    "睛彩青少": ["睛彩羽毛球"],
    "求索纪录": ["求索记录", "求索纪录4K", "求索记录4K", "求索纪录 4K", "求索记录 4K"],
    "金鹰纪实": ["湖南金鹰纪实", "金鹰记实"],
    "纪实科教": ["北京纪实科教", "BRTV纪实科教", "纪实科教8K"],
    "星空卫视": ["星空衛視", "星空衛视", "星空卫視"],
    "ChannelV": ["CHANNEL-V", "Channel[V]"],
    "凤凰卫视中文台": ["凤凰中文", "凤凰中文台", "凤凰卫视中文", "凤凰卫视"],
    "凤凰卫视香港台": ["凤凰香港台", "凤凰卫视香港", "凤凰香港"],
    "凤凰卫视资讯台": ["凤凰资讯", "凤凰资讯台", "凤凰咨询", "凤凰咨询台", "凤凰卫视咨询台", "凤凰卫视资讯", "凤凰卫视咨询"],
    "凤凰卫视电影台": ["凤凰电影", "凤凰电影台", "凤凰卫视电影", "鳳凰衛視電影台", " 凤凰电影"],
    "茶频道": ["湖南茶频道"],
    "快乐垂钓": ["湖南快乐垂钓"],
    "先锋乒羽": ["湖南先锋乒羽"],
    "天元围棋": ["天元围棋频道"],
    "汽摩": ["重庆汽摩", "汽摩频道", "重庆汽摩频道"],
    "梨园频道": ["河南梨园频道", "梨园", "河南梨园"],
    "文物宝库": ["河南文物宝库"],
    "武术世界": ["河南武术世界"],
    "乐游": ["乐游频道", "上海乐游频道", "乐游纪实", "SiTV乐游频道", "SiTV 乐游频道"],
    "欢笑剧场": ["上海欢笑剧场4K", "欢笑剧场 4K", "欢笑剧场4K", "上海欢笑剧场"],
    "生活时尚": ["生活时尚4K", "SiTV生活时尚", "上海生活时尚"],
    "都市剧场": ["都市剧场4K", "SiTV都市剧场", "上海都市剧场"],
    "游戏风云": ["游戏风云4K", "SiTV游戏风云", "上海游戏风云"],
    "金色学堂": ["金色学堂4K", "SiTV金色学堂", "上海金色学堂"],
    "动漫秀场": ["动漫秀场4K", "SiTV动漫秀场", "上海动漫秀场"],
    "卡酷少儿": ["北京KAKU少儿", "BRTV卡酷少儿", "北京卡酷少儿", "卡酷动画"],
    "哈哈炫动": ["炫动卡通", "上海哈哈炫动"],
    "优漫卡通": ["江苏优漫卡通", "优漫漫画"],
    "金鹰卡通": ["湖南金鹰卡通"],
    "中国交通": ["中国交通频道"],
    "中国天气": ["中国天气频道"],
    "华数4K": ["华数低于4K", "华数4K电影", "华数爱上4K"],
}

# ===============================
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

def get_isp_from_api(data):
    isp_raw = (data.get("isp") or "").lower()
    if "telecom" in isp_raw or "ct" in isp_raw or "chinatelecom" in isp_raw:
        return "电信"
    elif "unicom" in isp_raw or "cu" in isp_raw or "chinaunicom" in isp_raw:
        return "联通"
    elif "mobile" in isp_raw or "cm" in isp_raw or "chinamobile" in isp_raw:
        return "移动"
    return "未知"

def get_isp_by_regex(ip):
    if re.match(r"^(1[0-9]{2}|2[0-3]{2}|42|43|58|59|60|61|110|111|112|113|114|115|116|117|118|119|120|121|122|123|124|125|126|127|175|180|182|183|184|185|186|187|188|189|223)\.", ip):
        return "电信"
    elif re.match(r"^(8|9|10|11|12|13|14|15|16|17|18|19|20|21|22|23|24|25|26|27|28|29|30|31|32|33|34|35|40|41|44|45|46|47|48|49|50|51|52|53|54|55|56|57|62|63|64|65|66|67|68|69|70|71|72|73|74|75|76|77|78|79|80|81|82|83|84|85|86|87|88|89|90|91|92|93|94|95|96|97|98|99|100|101|102|103|104|105|106|107|108|109|128|129|130|131|132|133|140|141|142|143|144|145|146|147|148|149|150|151|152|153|154|155|156|157|158|159|160|161|162|163|164|165|166|167|168|169|170|171|172|173|174|176|177|178|179|190|191|192|193|194|195|196|197|198|199|200|201|202|203|204|205|206|207|208|209|210|211|212|213|214|215|216|217|218|219|220|221|222)\.", ip):
        return "联通"
    elif re.match(r"^(36|37|38|39|100|101|102|103|104|105|106|107|108|109|134|135|136|137|138|139|150|151|152|157|158|159|170|178|182|183|184|187|188|189)\.", ip):
        return "移动"
    return "未知"

# ===============================
# 第一阶段：读取IP并分类保存
def first_stage():
    os.makedirs(IP_DIR, exist_ok=True)
    all_ips = set()

    # 优先从本地 ip_urls.txt 读取IP
    if os.path.exists("ip_urls.txt"):
        print("📁 从本地 ip_urls.txt 读取IP...")
        try:
            with open("ip_urls.txt", "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if line.startswith("http://"):
                        ip_part = line.replace("http://", "").split("/")[0]
                        all_ips.add(ip_part)
                    else:
                        all_ips.add(line)
            print(f"✅ 从本地文件读取到 {len(all_ips)} 个IP")
        except Exception as e:
            print(f"⚠️ 读取本地文件失败：{e}")

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

    province_isp_dict = {}
    total_ips = 0

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
            total_ips += len(ip_set)
        except Exception as e:
            print(f"❌ 写入 {path} 失败：{e}")

    print(f"✅ 第一阶段完成，当前轮次：{count}，共写入 {total_ips} 个IP")
    return count


# ===============================
# ===== 16KB 深度吸血测流函数 =====
def check_stream_quality(url, min_bytes=16384, timeout=8):
    """
    16KB 强行吸血测流 - 对完整的 http://IP:端口/rtp/组播地址:端口 进行检测
    返回: (is_valid, bytes_received, error_msg)
    """
    try:
        start_time = time.time()
        
        response = requests.get(
            url, 
            stream=True, 
            timeout=timeout,
            headers={
                "User-Agent": "VLC/3.0.18 LibVLC/3.0.18",
                "Icy-MetaData": "1",
                "Connection": "close",
                "Accept": "*/*"
            }
        )
        
        if response.status_code != 200:
            return False, 0, f"HTTP {response.status_code}"
        
        content_type = response.headers.get('Content-Type', '').lower()
        if content_type and 'text' in content_type:
            return False, 0, "Content-Type: text/html"
        
        data_received = 0
        for chunk in response.iter_content(chunk_size=4096):
            data_received += len(chunk)
            if data_received >= min_bytes:
                return True, data_received, "OK"
            if time.time() - start_time > timeout:
                break
        
        return False, data_received, f"仅收到 {data_received} 字节"
        
    except requests.exceptions.ConnectTimeout:
        return False, 0, "连接超时"
    except requests.exceptions.ReadTimeout:
        return False, 0, "读取超时"
    except requests.exceptions.ConnectionError:
        return False, 0, "连接错误"
    except Exception as e:
        return False, 0, str(e)[:30]


# ===============================
# ===== 第二阶段：组合IP+rtp → 16KB深度测流 → 写入zubo.txt =====
def second_stage():
    print("🔔 第二阶段触发：组合IP+rtp → 16KB深度测流 → 生成 zubo.txt")
    
    if not os.path.exists(IP_DIR):
        print("⚠️ ip 目录不存在，跳过第二阶段")
        return

    if not os.path.exists(RTP_DIR):
        print("⚠️ rtp 目录不存在，跳过第二阶段")
        return

    # ===== 步骤1：收集所有候选完整URL，按IP分组 =====
    ip_groups = {}  # {ip_port: [(频道名, 完整URL), ...]}

    for ip_file in os.listdir(IP_DIR):
        if not ip_file.endswith(".txt"):
            continue

        ip_path = os.path.join(IP_DIR, ip_file)
        rtp_path = os.path.join(RTP_DIR, ip_file)

        if not os.path.exists(rtp_path):
            print(f"⏭️ 跳过 {ip_file}：rtp目录下无对应文件")
            continue

        try:
            with open(ip_path, encoding="utf-8") as f1:
                ip_lines = [x.strip() for x in f1 if x.strip()]
            with open(rtp_path, encoding="utf-8") as f2:
                rtp_lines = [x.strip() for x in f2 if x.strip()]
        except Exception as e:
            print(f"⚠️ 文件读取失败 {ip_file}：{e}")
            continue

        if not ip_lines or not rtp_lines:
            print(f"⏭️ 跳过 {ip_file}：IP或RTP为空")
            continue

        print(f"🔄 处理 {ip_file}：{len(ip_lines)} 个IP × {len(rtp_lines)} 个频道")

        for ip_port in ip_lines:
            for rtp_line in rtp_lines:
                if "," not in rtp_line:
                    continue

                ch_name, rtp_url = rtp_line.split(",", 1)

                if "rtp://" in rtp_url:
                    part = rtp_url.split("rtp://", 1)[1]
                    full_url = f"http://{ip_port}/rtp/{part}"
                    ip_groups.setdefault(ip_port, []).append((ch_name, full_url))
                elif "udp://" in rtp_url:
                    part = rtp_url.split("udp://", 1)[1]
                    full_url = f"http://{ip_port}/udp/{part}"
                    ip_groups.setdefault(ip_port, []).append((ch_name, full_url))

    if not ip_groups:
        print("⚠️ 没有生成任何候选URL")
        return

    total_channels = sum(len(v) for v in ip_groups.values())
    print(f"📊 共 {len(ip_groups)} 个IP，{total_channels} 条频道需要检测")

    # ===== 步骤2：对每个IP的所有完整URL进行16KB深度测流 =====
    print("🚀 启动16KB深度吸血测流（每个URL检测）...")
    
    ip_results = {}  # {ip_port: {'valid_urls': [(ch_name, url)], 'invalid_count': int}}
    valid_ips = set()
    
    def detect_ip_channels(ip_port, entries):
        """检测一个IP的所有频道URL"""
        valid_urls = []
        invalid_count = 0
        
        for ch_name, url in entries:
            is_valid, bytes_received, error = check_stream_quality(url, min_bytes=16384, timeout=8)
            if is_valid:
                valid_urls.append((ch_name, url))
                print(f"  ✅ {ch_name} - {url[:60]}... (收到 {bytes_received} 字节)")
            else:
                invalid_count += 1
                if invalid_count <= 3:
                    print(f"  ❌ {ch_name} - {error}")
        
        return ip_port, valid_urls, invalid_count

    processed = 0
    total_ips = len(ip_groups)
    total_valid_urls = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(detect_ip_channels, ip_port, entries): ip_port 
            for ip_port, entries in ip_groups.items()
        }
        
        for future in concurrent.futures.as_completed(futures):
            processed += 1
            ip_port = futures[future]
            
            try:
                ip, valid_urls, invalid_count = future.result()
                ip_results[ip] = {
                    'valid_urls': valid_urls,
                    'invalid_count': invalid_count
                }
                if valid_urls:
                    valid_ips.add(ip)
                    total_valid_urls += len(valid_urls)
            except Exception as e:
                print(f"⚠️ 检测IP {ip_port} 时异常：{e}")
                ip_results[ip_port] = {
                    'valid_urls': [],
                    'invalid_count': len(ip_groups[ip_port])
                }
            
            if processed % 5 == 0 or processed == total_ips:
                print(f"⏳ 检测进度：{processed}/{total_ips} | 有效IP: {len(valid_ips)}")

    print(f"✅ 测流完成：有效IP {len(valid_ips)} 个，有效频道 {total_valid_urls} 条")

    # ===== 步骤3：只保留有效IP的所有频道，写入zubo.txt =====
    if not valid_ips:
        print("⚠️ 没有检测到任何有效的IP，zubo.txt 为空")
        with open(ZUBO_FILE, "w", encoding="utf-8") as f:
            f.write("# 没有检测到有效的流\n")
        return

    all_valid_entries = []
    for ip_port in valid_ips:
        all_valid_entries.extend(ip_results[ip_port]['valid_urls'])

    unique = {}
    for ch_name, url in all_valid_entries:
        if url not in unique:
            unique[url] = (ch_name, url)

    try:
        with open(ZUBO_FILE, "w", encoding="utf-8") as f:
            for ch_name, url in unique.values():
                f.write(f"{ch_name},{url}\n")
        print(f"🎯 第二阶段完成：写入 {len(unique)} 条有效频道到 zubo.txt")
        print(f"   (来自 {len(valid_ips)} 个有效IP)")
    except Exception as e:
        print(f"❌ 写 zubo.txt 失败：{e}")


# ===============================
# ===== 第三阶段：从zubo.txt生成IPTV.txt =====
def third_stage():
    print("🧩 第三阶段：从 zubo.txt 生成 IPTV.txt")
    
    if not os.path.exists(ZUBO_FILE):
        print("⚠️ zubo.txt 不存在，跳过第三阶段")
        return

    try:
        with open(ZUBO_FILE, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    except Exception as e:
        print(f"❌ 读取 zubo.txt 失败：{e}")
        return

    if not lines:
        print("⚠️ zubo.txt 为空，跳过第三阶段")
        return

    ip_info = {}
    if os.path.exists(IP_DIR):
        for fname in os.listdir(IP_DIR):
            if not fname.endswith(".txt"):
                continue
            province_operator = fname.replace(".txt", "")
            try:
                with open(os.path.join(IP_DIR, fname), encoding="utf-8") as f:
                    for line in f:
                        ip_port = line.strip()
                        if ip_port:
                            ip_info[ip_port] = province_operator
            except Exception as e:
                print(f"⚠️ 读取 {fname} 失败：{e}")

    processed_lines = []
    for line in lines:
        if "," not in line:
            continue
        ch_name, url = line.split(",", 1)
        
        m = re.match(r"http://([^/]+)/", url)
        if m:
            ip_port = m.group(1)
            operator = ip_info.get(ip_port, "未知")
            processed_lines.append(f"{ch_name},{url}${operator}")
        else:
            processed_lines.append(f"{ch_name},{url}${'未知'}")

    beijing_now = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
    disclaimer_url = "http://kakaxi.indevs.in/LOGO/Disclaimer.mp4"

    try:
        with open(IPTV_FILE, "w", encoding="utf-8") as f:
            f.write(f"更新时间: {beijing_now}（北京时间）\n\n")
            f.write("更新时间,#genre#\n")
            f.write(f"{beijing_now},{disclaimer_url}\n\n")

            for category, ch_list in CHANNEL_CATEGORIES.items():
                f.write(f"{category},#genre#\n")
                matched_count = 0
                for ch in ch_list:
                    for line in processed_lines:
                        name = line.split(",", 1)[0]
                        if name == ch:
                            f.write(line + "\n")
                            matched_count += 1
                            break
                if matched_count > 0:
                    f.write("\n")
        print(f"🎯 IPTV.txt 生成完成，共 {len(processed_lines)} 条频道")
    except Exception as e:
        print(f"❌ 写 IPTV.txt 失败：{e}")


# ===============================
# 文件推送
def push_all_files():
    print("🚀 推送所有更新文件到 GitHub...")
    try:
        os.system('git config --global user.name "github-actions"')
        os.system('git config --global user.email "github-actions@users.noreply.github.com"')
    except Exception:
        pass

    os.system("git add 计数.txt || true")
    os.system("git add ip/*.txt || true")
    os.system("git add zubo.txt || true")
    os.system("git add IPTV.txt || true")
    os.system('git commit -m "自动更新：16KB深度测流，过滤无效IP" || echo "⚠️ 无需提交"')
    os.system("git push origin main || echo "⚠️ 推送失败"")


# ===============================
# 主执行逻辑
if __name__ == "__main__":
    print("🚀 脚本启动...")
    
    os.makedirs(IP_DIR, exist_ok=True)
    os.makedirs(RTP_DIR, exist_ok=True)

    current_count = get_run_count()
    print(f"📊 当前计数：{current_count}")
    
    if current_count >= 72:
        print("🗑️ 已满24小时，清空ip目录...")
        if os.path.exists(IP_DIR):
            for file in os.listdir(IP_DIR):
                if file.endswith('.txt'):
                    os.remove(os.path.join(IP_DIR, file))
        save_run_count(0)
        current_count = 0

    run_count = first_stage()
    
    if run_count is None:
        run_count = 0

    if run_count > 0 and run_count % 10 == 0:
        print(f"🎯 达到触发条件（{run_count} 是 10 的倍数），执行第二、三阶段")
        second_stage()
        third_stage()
    else:
        print(f"ℹ️ 当前计数 {run_count}，不是 10 的倍数或未获取到IP，跳过第二、三阶段")

    push_all_files()
