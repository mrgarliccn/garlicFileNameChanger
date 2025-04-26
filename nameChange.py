import os
import re
from pathlib import Path
from collections import defaultdict

# ====================== 工具函数定义 ======================
SEGMENT_PATTERNS = [
    r'([a-zA-Z])$',              # 字母后缀
    r'([上中下])$',               # 中文后缀
    r'[\[\(]([a-zA-Z上中下])[\]\)]' # 带符号的标识
]

def extract_tags(filename_part, symbol_type):
    """根据符号类型提取有效标签"""
    patterns = {
        1: r'\[(.*?)\]',    # 半角方括号
        2: r'\((.*?)\)',    # 半角括号
        3: r'【(.*?)】',    # 全角方括号
        4: r'\.(.*?)\.',    # 点分符号
        5: None             # 无特殊符号
    }
    
    if symbol_type == 5:
        return re.findall(r'(?<!\d)(\d{2,})(?!\d)', filename_part)  # 精确匹配连续数字
    
    pattern = patterns.get(symbol_type)
    raw_tags = re.findall(pattern, filename_part) if pattern else []
    
    # 过滤有效剧集标签（排除分辨率等无关数字）
    valid_tags = []
    for tag in raw_tags:
        if re.match(r'^(S\d+E\d+|SE\d+|\d+[a-zA-Z]?|[上中下]?)$', tag):
            valid_tags.append(tag)
    return valid_tags

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
    
    # 精确匹配集数数字
    digit_tags = [t for t in tags if re.match(r'^\d+$', t)]
    if digit_tags:
        result['episode'] = max(map(int, digit_tags))  # 取最大数值
        return result
    
    # 无符号模式特殊处理
    if symbol_type == 5:
        if match := re.search(r'(\d+)(\D+)$', filename):
            result['episode'] = int(match.group(1))
            result['segment'] = match.group(2).strip()
    
    return result

def generate_new_name(series_name, ep_info, ext, counter, custom_season=None):
    """生成新文件名"""
    base = series_name
    
    # 优先使用自动检测的季数
    if ep_info['season'] is not None:
        base += f"_第{ep_info['season']}季"
    elif custom_season:
        base += f"_{custom_season}"
    
    if ep_info['episode'] is not None:
        base += f"_第{ep_info['episode']}集"
    
    # 处理分段标识
    if ep_info['segment']:
        base += f"_{ep_info['segment']}"
    elif counter[ep_info['episode']] > 1:
        base += f"_{chr(96 + counter[ep_info['episode']])}"  # 自动生成a,b,c
    
    return f"{base}.{ext}" if ext else base

def print_report(report):
    """统一打印检测报告"""
    print("\n" + "="*60)
    categories = [
        ('valid', '可修改文件'),
        ('no_tag', '未识别文件'),
        ('conflict', '命名冲突文件')
    ]
    
    for key, title in categories:
        if report[key]:
            print(f"\n[{title}]")
            for item in report[key]:
                if key == 'valid':
                    print(f"  {item[0]} → {item[1]}")
                else:
                    print(f"  {item}")

# ====================== 主程序逻辑 ======================
def main():
    report = defaultdict(list)
    try:
        # ==== 用户输入阶段 ====
        print("=== 剧集文件重命名工具 ===")
        dir_path = Path(input("请输入文件夹绝对路径：").strip())
        
        # 路径验证
        if not dir_path.exists():
            print(f"错误：路径 '{dir_path}' 不存在")
            return
        if not dir_path.is_dir():
            print(f"错误：'{dir_path}' 不是有效文件夹")
            return
        
        print("\n请选择标签符号类型：")
        print("1. 半角方括号[]\n2. 半角括号()\n3. 全角方括号【】\n4. 点分符号\n5. 无特殊符号")
        symbol_type = int(input("请输入选项数字(1-5)："))
        
        series_name = input("\n请输入剧集名称：").strip()

        # ==== 文件处理阶段 ====
        episodes = []
        has_auto_season = False
        existing_files = {f.name for f in dir_path.iterdir()}
        
        # 第一次扫描：收集剧集信息
        for file_path in dir_path.iterdir():
            if not file_path.is_file():
                continue
                
            filename = file_path.name
            basename, ext = os.path.splitext(filename)
            ext = ext.lstrip('.')
            
            # 提取标签并分析
            tags = extract_tags(basename, symbol_type)
            ep_info = analyze_episode(basename, tags, symbol_type)
            
            # 记录季数信息
            if ep_info['season'] is not None:
                has_auto_season = True
            
            if ep_info['episode'] is None:
                report['no_tag'].append(filename)
                continue
                
            episodes.append((file_path, ep_info, ext))

        # ==== 生成初始方案 ====
        counter = defaultdict(int)
        initial_plan = []
        for file_path, ep_info, ext in episodes:
            counter[ep_info['episode']] += 1
        
        # 生成初始名称
        generated_names = set()
        for file_path, ep_info, ext in episodes:
            if counter[ep_info['episode']] > 1 and not ep_info['segment']:
                ep_info['segment'] = parse_segment(str(ep_info['episode']), ep_info['raw'])
            
            new_name = generate_new_name(series_name, ep_info, ext, counter)
            
            # 冲突检测
            if new_name in existing_files or new_name in generated_names:
                report['conflict'].append((file_path.name, new_name))
                continue
            
            generated_names.add(new_name)
            initial_plan.append((file_path, new_name))
            report['valid'].append((file_path.name, new_name))

        # ==== 输出初始报告 ====
        print_report(report)
        
        # ==== 自定义季数处理 ====
        custom_season = None
        if not has_auto_season:
            choice = input("\n检测到无季数信息，是否添加自定义季数？(Y/N 默认N): ").strip().upper()
            if choice == 'Y':
                while True:
                    custom_season = input("请输入完整季数文本（如：第一季）: ").strip()
                    if not custom_season:
                        print("输入为空，将不添加季数信息")
                        break
                    if re.search(r'[\\/:*?"<>|]', custom_season):
                        print("季数包含非法字符，请重新输入")
                        continue
                    break
                
                # 重新生成最终方案
                report = defaultdict(list)
                final_plan = []
                generated_names = set()
                
                for file_path, ep_info, ext in episodes:
                    new_name = generate_new_name(series_name, ep_info, ext, counter, custom_season)
                    
                    # 冲突检测（包含已有文件和新生成文件）
                    if new_name in existing_files or new_name in generated_names:
                        report['conflict'].append((file_path.name, new_name))
                        continue
                    
                    generated_names.add(new_name)
                    final_plan.append((file_path, new_name))
                    report['valid'].append((file_path.name, new_name))
                
                # 输出最终报告
                print("\n" + "="*60)
                print("[ 最终修改方案 ]")
                print_report(report)
                rename_plan = final_plan
            else:
                rename_plan = initial_plan
        else:
            rename_plan = initial_plan

        # ==== 用户确认 ====
        if not rename_plan:
            print("\n没有需要修改的文件")
            return
            
        confirm = input("\n是否确认执行修改？(Y/N): ").upper()
        if confirm != 'Y':
            print("操作已取消")
            return
            
        # ==== 执行重命名 ====
        print("\n正在执行重命名...")
        success = 0
        for file_path, new_name in rename_plan:
            try:
                file_path.rename(file_path.parent / new_name)
                print(f"✓ 重命名成功：{file_path.name} → {new_name}")
                success += 1
            except Exception as e:
                print(f"✗ 重命名失败：{file_path.name} → {new_name} ({str(e)})")
        print(f"\n操作完成，成功重命名 {success}/{len(rename_plan)} 个文件")
        
    except Exception as e:
        print(f"\n程序运行出错：{str(e)}")

# ====================== 主程序入口 ======================
if __name__ == "__main__":
    main()