import os
import shutil

base = os.path.dirname(os.path.abspath(__file__))
src_html = os.path.join(base, 'app', 'templates', 'index.html')
dst_html = os.path.join(base, 'index.html')

with open(src_html, 'r', encoding='utf-8') as f:
    content = f.read()

# Make all paths relative for GitHub Pages
content = content.replace('href="/static/', 'href="static/')
content = content.replace('src="/static/', 'src="static/')
content = content.replace('href="/manifest.json"', 'href="static/manifest.json"')

with open(dst_html, 'w', encoding='utf-8') as f:
    f.write(content)

src_static = os.path.join(base, 'app', 'static')
dst_static = os.path.join(base, 'static')
if os.path.exists(dst_static):
    shutil.rmtree(dst_static)
shutil.copytree(src_static, dst_static)

# Also update sw.js inside static/ to use relative paths
sw_path = os.path.join(dst_static, 'sw.js')
if os.path.exists(sw_path):
    with open(sw_path, 'r', encoding='utf-8') as f:
        sw_code = f.read()
    sw_code = sw_code.replace("'/static/", "'static/")
    with open(sw_path, 'w', encoding='utf-8') as f:
        f.write(sw_code)

print("SUCCESS: index.html and static folder created at root!")
