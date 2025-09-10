import os
import tempfile
from bypy import ByPy

# 初始化bypy对象
bp = ByPy()

# 上传文件到百度网盘
def upload_file(local_path, remote_path):
    """
    上传文件到百度网盘
    Args:
        local_path: 本地文件路径
        remote_path: 百度网盘目标路径
    Returns:
        int: 0表示成功，其他值表示失败
    """
    try:
        if not os.path.exists(local_path):
            print(f"错误：本地文件 {local_path} 不存在")
            return -1
            
        result = bp.upload(local_path, remote_path)
        if result == 0:
            print(f"文件 {local_path} 上传成功到 {remote_path}")
        else:
            print(f"文件上传失败，错误码: {result}")
        return result
    except Exception as e:
        print(f"上传文件时发生错误: {e}")
        return -1
        
def share_file(remote_path):
    """
    分享百度网盘中的文件并获取分享链接和提取码
    Args:
        remote_path: 百度网盘中的文件路径
    Returns:
        tuple: (分享链接, 提取码) 如果分享失败返回 (None, None)
    """
    try:
        # 先检查文件是否存在于网盘中
        meta = bp.meta(remote_path)
        if not meta or 'error_code' in meta:
            print(f"错误：文件 {remote_path} 在网盘中不存在")
            return None, None

        # 直接使用创建分享链接的接口
        result = bp.share([remote_path], pwd=None)
        print(f'share result:{result}')
        if result and isinstance(result, list) and len(result) > 0:
            share_info = result[0]
            share_url = share_info.get('link', '')
            share_pwd = share_info.get('pwd', '')
            if share_url:
                print(f"文件分享成功！")
                print(f"分享链接: {share_url}")
                if share_pwd:
                    print(f"提取码: {share_pwd}")
                return share_url, share_pwd
            
        print("分享失败或未获取到分享链接")
        return None, None
    except Exception as e:
        print(f"分享文件时发生错误: {e}")
        return None, None

# 从百度网盘下载文件
def download_file(remote_path, local_path):
    try:
        result = bp.download(remote_path, local_path)
        if result == 0:
            print(f"文件 {remote_path} 下载成功到 {local_path}")
        else:
            print(f"文件下载失败，错误码: {result}")
    except Exception as e:
        print(f"下载文件时发生错误: {e}")

# 示例使用
if __name__ == "__main__":
    try:
        # 上传文件示例
        local_file = "test_downloads/1.pdf"  # 本地文件路径
        remote_dir = "/apps/bypy/"  # 百度网盘目标路径
        remote_path = "/apps/bypy/1.pdf"
        
        # 检查本地文件是否存在
        if not os.path.exists(local_file):
            print(f"错误：本地文件 {local_file} 不存在")
            exit(1)
            
        # 分享文件并获取分享链接
        share_url, share_pwd = share_file(remote_path)
        if share_url:
                print(f"\n文件分享信息:")
                print(f"链接：{share_url}")
                if share_pwd:
                    print(f"提取码：{share_pwd}")
    except Exception as e:
        print(f"程序执行出错: {e}")
