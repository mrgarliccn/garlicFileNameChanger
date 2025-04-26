import os
import re
from pathlib import Path
from collections import defaultdict

# 分段标识匹配规则
SEGMENT_PATTERNS = [
    r'([a-zA-Z])$',              # 字母后缀
    r'([上中下])$',               # 中文后缀
    r'[\[\(]([a-zA-Z上中下])[\]\)]' # 带符号的标识
]

def extract_tags(filename_part, symbol_type):
    """根据符号类型提取标签"""
    patterns = {
        1: r'\[(.*?)\]',    # 半角方括号
        2: r'\((.*?)\)',    # 半角括号
        3: r'【(.*?)】',    # 全角方括号
        4: r'\.(.*?)\.',    # 点分符号
        5: None             # 无特殊符号
    }
    
    if symbol_type == 5:
        return re.findall(r'\d+', filename_part)
    
    pattern = patterns.get(symbol_type)
    return re.findall(pattern, filename_part) if pattern else []

def parse_segment(ep_str, filename):
    """解析分段标识"""
    for pattern in SEGMENT_PATTERNS:
        match = re.search(ep_str + pattern, filename)
        if match:
            return match.group(1)
    return None

def analyze_episode(filename, tags, symbol_type):
    """分析剧集信息并返回数据结构"""
    result = {
        'season': None,
        'episode': None,
        'segment': None,
        'raw': filename
    }
    
    # 优先解析季集格式
    for tag in tags:
        if match := re.match(r'^[sS](\d+)[eE](\d+)(\D*)$', tag):
            result['season'] = int(match.group(1))
            result['episode'] = int(match.group(2))
            result['segment'] = match.group(3).lower() or None
            return result
    
    # 解析数字+分段标识
    for tag in tags:
        if match := re.match(r'^(\d+)(\D+)$', tag):
            result['episode'] = int(match.group(1))
            result['segment'] = match.group(2).strip()
            return result
        if tag.isdigit():
            result['episode'] = int(tag)
    
    # 无符号模式特殊处理
    if symbol_type == 5:
        if match := re.search(r'(\d+)(\D+)$', filename):
            result['episode'] = int(match.group(1))
            result['segment'] = match.group(2).strip()
    
    return result

def generate_new_name(series_name, ep_info, ext, counter):
    """生成新文件名"""
    base = series_name
    if ep_info['season']:
        base += f"_第{ep_info['season']}季"
    if ep_info['episode'] is not None:
        base += f"_第{ep_info['episode']}集"
    if ep_info['segment']:
        base += f"_{ep_info['segment']}"
    elif counter[ep_info['episode']] > 1:
        base += f"_{chr(96 + counter[ep_info['episode']])}"  # 自动生成a,b,c
    
    return f"{base}.{ext}" if ext else base

def main():
    # 初始化系统
    report = defaultdict(list)
    dir_path = Path(input("请输入文件夹绝对路径：").strip())
    
    if not dir_path.is_dir():
        print("路径无效")
        return
    
    print("\n请选择标签符号类型：")
    symbol_type = int(input("1.半角[] 2.半角() 3.全角【】 4.点分 5.无符号\n选项："))
    series_name = input("\n请输入剧集名称：").strip()
    
    # 收集所有剧集信息
    episodes = []
    for file_path in dir_path.iterdir():
        if not file_path.is_file():
            continue
        
        filename = file_path.name
        basename, ext = os.path.splitext(filename)
        ext = ext.lstrip('.')
        
        tags = extract_tags(basename, symbol_type)
        ep_info = analyze_episode(basename, tags, symbol_type)
        
        if ep_info['episode'] is None:
            report['no_tag'].append(filename)
            continue
        
        episodes.append((file_path, ep_info, ext))
    
    # 检测重复并生成名称
    counter = defaultdict(int)
    rename_plan = []
    for file_path, ep_info, ext in episodes:
        counter[ep_info['episode']] += 1
    
    for file_path, ep_info, ext in episodes:
        # 生成分段标识
        if counter[ep_info['episode']] > 1 and not ep_info['segment']:
            ep_info['segment'] = parse_segment(str(ep_info['episode']), ep_info['raw'])
        
        new_name = generate_new_name(series_name, ep_info, ext, counter)
        
        # 冲突处理
        if (file_path.parent / new_name).exists():
            report['conflict'].append((file_path.name, new_name))
            continue
        
        rename_plan.append((file_path, new_name))
        report['valid'].append((file_path.name, new_name))
    
    # 输出报告
    print("\n" + "="*60)
    for category in ['valid', 'no_tag', 'conflict']:
        if report[category]:
            print(f"\n[{category}]")
            for item in report[category]:
                print(f"  {item[0]} → {item[1]}" if category == 'valid' else f"  {item}")
    
    # 用户确认
    if input("\n确认修改？(Y/N): ").upper() != 'Y':
        print("操作取消")
        return
    
    # 执行重命名
    print("\n正在重命名...")
    for file_path, new_name in rename_plan:
        try:
            file_path.rename(file_path.parent / new_name)
            print(f"成功：{file_path.name} → {new_name}")
        except Exception as e:
            print(f"失败：{str(e)}")

if __name__ == "__main__":
    main()