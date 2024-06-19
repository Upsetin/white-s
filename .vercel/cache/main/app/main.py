import os
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request
import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import os
import markdown
from loguru import logger
import markdown2

app = FastAPI()

BLOG_DIR = "app/blogs"
IMAGE_DIR = "app/images"

# 挂载静态文件路径
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/images", StaticFiles(directory=IMAGE_DIR), name="images")

# 设置Jinja2模板文件路径
templates = Jinja2Templates(directory="app/templates")

# init the index
blog_meta_data = []
for md_file_path in os.listdir(BLOG_DIR):
    if not md_file_path.endswith(".md"):
        continue

    metadata = {}
    with open(os.path.join(BLOG_DIR, md_file_path), "r", encoding="utf-8") as file:
        lines = file.readlines()
    if lines[0].strip() == '---':
        i = 1
        while i < len(lines) and lines[i].strip() != '---':
            line = lines[i].strip()
            key, value = line.split(':', 1)
            metadata[key.strip()] = value.strip()
            i += 1
        blog_meta_data.append(
            {
                "title": metadata.get("title", "Unknow"),
                "publishTime": metadata.get("publishTime", "Unknow"),
                "slug": md_file_path.strip(".md"),
            },
        )
# read local files
with open("./app/blogs/index.json", "w") as f:
    f.write(json.dumps(blog_meta_data, indent=4))

logger.debug("init the blog metadata successfully!")

@app.get("/")
async def read_root(request: Request):
    # read local files
    with open("./app/blogs/index.json") as f:
        blog_list_metadata = json.loads(f.read())

    print(blog_list_metadata)
    return templates.TemplateResponse("index.html", {"blog_list_metadata": blog_list_metadata, "request": request})


@app.get("/blog/{slug}", response_class=HTMLResponse)
def read_blog(request: Request, slug: str):
    # read local files
    with open("./app/blogs/index.json") as f:
        blog_list_metadata = json.loads(f.read())

    slug_info = {i["slug"]: i for i in blog_list_metadata}

    if slug not in  slug_info:
        raise HTTPException(status_code=404, detail="not found")

    # 构建文件路径
    file_path = os.path.join(BLOG_DIR, f"{slug}.md")

    # 检查文件是否存在
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Blog not found")

    # 读取 Markdown 文件内容
    with open(file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()

    # 提取元数据部分
    metadata = {}
    if lines[0].strip() == '---':
        i = 1
        while i < len(lines) and lines[i].strip() != '---':
            line = lines[i].strip()
            key, value = line.split(':', 1)
            metadata[key.strip()] = value.strip()
            i += 1
        content_lines = lines[i+1:]
    else:
        content_lines = lines

    # 将 Markdown 转换为 HTML
    markdown_content = ''.join(content_lines)
    html_content = markdown2.markdown(markdown_content, extras=['fenced-code-blocks'])
    print(html_content)
    return templates.TemplateResponse("blog_detail_template.html",         {
        "request": request,
        "title": metadata.get('title', 'Unknown'),
        "content": html_content,
        "author": metadata.get('author', 'White'),
        "publishTime": metadata.get('publishTime', 'Unknown')
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)
