import os
import requests
import re
import uuid
import base64
import sys
import time
black_url_list = []
dirPath = './test_md'
markdown_list = []
img_dict = {
    "no_image": [],
    "image": []
}

def get_markdown_list(source_md_path):
    with open(source_md_path, "r") as f:
        # 读取源文件
        source_md_content = f.read()
        des_md_content = source_md_content
        # 正则匹配，获得urls列表
        source_md_img_url_list = re.findall(r'(?:!\[(.*?)\]\((.*?)\))', source_md_content)
        return source_md_img_url_list

def search_sameSuffix_file(dirPath):
    '''
    查找指定文件夹下所有相同后缀名的文件
    @param dirPath: markdown目录
    @return markdown_list: MD文档列表
    '''
    suffix = 'md'
    dirs = os.listdir(dirPath)
    for currentFile in dirs:
        fullPath = dirPath + '/' + currentFile
        if os.path.isdir(fullPath):
            search_sameSuffix_file(fullPath)
        elif currentFile.split('.')[-1] == suffix:
            markdown_list.append(fullPath)


def img_base64(path):
    '''
    图床base64处理
    :param path: 图片路径
    :return: 图片base64内容
    '''
    f = open(path, 'rb')
    ls_f = base64.b64encode(f.read())
    f.close()
    return (ls_f)

def uploadImageToChevereto(filepath, preseverd_mode=True, force_mode=False):
    '''
    上床图片到图床
    :param filename: 图片路径
    :return: 图床链接
    '''
    imgurl = ''
    img = img_base64(filepath)  # 图像转换成base64
    # 设置请求内容
    data = {
        "source": img,
        "url": '',
        "key": "",  # API v1 的密钥
        "format": 'json'  # 设置返回格式 [value：json(默认值)，redirect，txt]
    }
    # 开始请求内容
    response_content = {}
    res = requests.post(data['url'], data=data).json()
    if res is not None:
        if res['status_code'] == 200:
            imgurl = res['image']['url']
            response_content['status'] = 200
            response_content['content'] = imgurl
        else:
            if res['error']['message'] == "Can't get target upload source info":
                black_url = filepath.replace('http://', "").replace("https://", "").split("/")[0].replace("_", ".")
                if black_url not in black_url_list:
                    print(black_url)
                    black_url_list.append(black_url)
                    print(black_url_list)
            response_content['status'] = 404
            response_content['content'] = res['error']['message']
    else:
        print('request失败！')
    #  删除临时图片
    if not preseverd_mode:
        os.remove(filepath)
    return response_content['status'], response_content['content']

def uploadImageFromMarkdown(src_md_path):
    des_md_father_folder = './new_md'
    des_md_children_folder = "/".join(src_md_path.split('/')[:-1]) + '/'
    src_img_url_list = get_markdown_list(src_md_path)
    with open(src_md_path, "r") as f:
        # 读取源文件
        src_md_content = f.read()
        des_md_content = src_md_content
    for i in range(len(src_img_url_list)):
        # 遍历文档输出
        print("\r", end="")
        print("遍历文档", src_md_path.split('/')[-1], ":", i+1, "/", len(src_img_url_list), end="")

        src_img_url = src_img_url_list[i][1]
        src_img_host = src_img_url.replace("http://", "").replace("https://", "").split('/')[0]
        if src_img_host in black_url_list:
            print('发现疑似无效图床:', src_img_host)
            continue
        if "." in src_img_url.split('/')[-1]: # url是纯图片链接
            father = src_img_host.replace('.', '_')
            children_folder = "/".join(src_img_url.replace("http://", "").replace("https://", "").split('/')[1:-1])
            file_name = src_img_url.replace("http://", "").replace("https://", "").split('/')[-1]
        else: # url不是纯图片链接
            father = "./temp_img"
            children_folder = ""
            file_name = str(uuid.uuid1()) + "png"
        des_img_folder = os.path.join(father, children_folder)
        des_img_path = os.path.join(des_img_folder, file_name)
        # 创建子文件夹
        if not os.path.exists(des_img_folder):
            os.makedirs(des_img_folder)
        # 请求并下载图片内容
        try:
            r = requests.get(src_img_url)
            if r.status_code != 200:
                raise ConnectionError("test")
        except:
            print("图片下载异常！请检查网络状态")
            if src_img_host not in black_url_list:
                print(src_img_host)
                black_url_list.append(src_img_host)
                print(black_url_list)
                continue
        with open(des_img_path, 'wb') as f:
            f.write(r.content)
        # 图片上传，获取url
        temp_status, des_md_img_url = uploadImageToChevereto(des_img_path)
        if temp_status != 200:
            print("图片上传异常！原因为", des_md_img_url)
            continue
        # 开始替换markdown内容
        des_md_content = des_md_content.replace(src_img_url, des_md_img_url)
        if i != len(src_img_url_list) -1:
            sys.stdout.flush()
            time.sleep(0.05)
        else:
            print()
    # 开始写入markdown文件
    des_md_folder = os.path.join(des_md_father_folder, des_md_children_folder)
    des_md_path = os.path.join(des_md_father_folder, src_md_path)
    # 创建md子文件夹
    if not os.path.exists(des_md_folder):
        os.makedirs(des_md_folder)
    # 写入新md文件
    with open(des_md_path, 'w') as f:
        f.write(des_md_content)


print('正在获取Markdown文件列表...')
search_sameSuffix_file(dirPath)
print("目录",dirPath,"下的MD文件有",len(markdown_list),"个")
print("--------------------------")
print("开始遍历",dirPath,"下的文档")



# 获取Markdown文档图片链接
for md_url in markdown_list:
    img_list = get_markdown_list(md_url)
    if len(img_list) == 0:
        img_dict["no_image"].append(md_url)
    else:
        img_dict["image"].append(md_url)

print("开始上传有图文档:")
for md_url in img_dict["image"]:
    uploadImageFromMarkdown(md_url)