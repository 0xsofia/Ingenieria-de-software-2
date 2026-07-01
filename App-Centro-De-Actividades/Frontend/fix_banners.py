import os
import re

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find <div className="banner..." ...>...</div> that do NOT already have banner__close inside them
    # Because some might be nested, we can use a simpler approach:
    # We look for `<div[^>]*className=["\'][^"\']*banner[^"\']*["\'][^>]*>(.*?)</div>`
    # and only replace if it doesn't contain banner__close.
    
    pattern = re.compile(r'(<div[^>]*className=["\'][^"\']*banner[^"\']*["\'][^>]*>)(.*?)(</div>)', re.DOTALL)
    
    def repl(match):
        open_tag = match.group(1)
        inner = match.group(2)
        close_tag = match.group(3)
        
        if 'banner__close' in inner:
            return match.group(0) # Already processed
            
        close_btn = '<button type="button" className="banner__close" onClick={(e) => e.target.closest(\'.banner\').style.display = \'none\'}>×</button>'
        return f'{open_tag}{inner}{close_btn}{close_tag}'
    
    new_content, count = pattern.subn(repl, content)
    
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated div banners in {filepath}")

for root, _, files in os.walk('src'):
    for file in files:
        if file.endswith('.jsx'):
            process_file(os.path.join(root, file))

