# 电子书库 (EBooks Library)

一个功能全面的 Python 库，支持从多个平台搜索和下载电子书。

## 功能特性

- **多平台支持**：支持从 5+ 个电子书平台搜索和下载
- **异步支持**：采用现代 Python async/await 模式构建
- **类型提示**：完整的类型提示，提供更好的开发体验
- **统一 API**：所有平台使用统一接口
- **灵活配置**：易于配置和扩展
- **命令行工具**：提供命令行界面，方便快速操作

## 支持的平台

| 平台 | 搜索 | 下载 | 需要认证 |
|------|------|------|----------|
| Archive.org | ✅ | ✅ | 否 |
| Liber3 | ✅ | ✅ | 否 |
| Calibre-Web | ✅ | ✅ | 否* |
| Z-Library | ✅ | ✅ | 是 |
| Anna's Archive | ✅ | ⚠️** | 否 |

*需要本地 Calibre-Web 服务器  
**仅提供下载链接

## 安装

### 从 PyPI 安装（发布后）
```bash
pip install ebooks-library
```

### 从源码安装
```bash
git clone <repository-url>
cd astrbot_plugin_ebooks
pip install -e .
```

### 开发环境安装
```bash
git clone <repository-url>
cd astrbot_plugin_ebooks
pip install -e .[dev]
```

## 快速开始

### 基础使用

```python
import asyncio
from ebooks_library import EbooksLibrary

async def main():
    # 创建库实例
    library = EbooksLibrary()
    
    try:
        # 搜索电子书
        results = await library.search("Python编程", limit=5)
        
        print(f"找到 {len(results)} 本书:")
        for result in results:
            book = result.book_info
            print(f"- {book.title} 作者：{book.authors} ({result.platform.value})")
        
        # 下载第一个结果
        if results:
            download_result = await library.download(
                results[0].download_info,
                save_path="./downloads"
            )
            
            if download_result.success:
                print(f"下载完成: {download_result.file_name}")
            
    finally:
        await library.close()

# 运行示例
asyncio.run(main())
```

### 自定义配置

```python
from ebooks_library import EbooksLibrary, LibraryConfig, Platform

# 创建自定义配置
config = LibraryConfig(
    enable_archive=True,
    enable_liber3=True,
    enable_calibre=True,
    calibre_web_url="http://localhost:8083",
    max_results=20,
    timeout=30
)

async with EbooksLibrary(config) as library:
    # 搜索特定平台
    results = await library.search(
        "机器学习",
        platforms=[Platform.ARCHIVE_ORG, Platform.LIBER3],
        limit=10
    )
    
    for result in results:
        print(f"{result.book_info.title} ({result.platform.value})")
```

### Z-Library 认证

```python
config = LibraryConfig(
    enable_zlib=True,
    zlib_email="your_email@example.com",
    zlib_password="your_password"
)

async with EbooksLibrary(config) as library:
    results = await library.search("数据科学", limit=5)
    
    # 使用 ID 和哈希下载
    for result in results:
        if result.platform == Platform.ZLIBRARY:
            download_result = await library.download(result.download_info)
            if download_result.success:
                print(f"下载完成: {download_result.file_name}")
```

## 命令行界面

### 搜索电子书
```bash
# 基础搜索
ebooks-search "Python编程"

# 搜索特定平台
ebooks-search "机器学习" -p archive_org liber3

# 限制结果数量
ebooks-search "数据科学" -l 5

# 使用自定义配置
ebooks-search "编程" -c config.json
```

### 下载电子书
```bash
# 通过 URL 下载
ebooks-download "https://archive.org/download/book-id/book.pdf"

# 通过 ID 下载（自动检测平台）
ebooks-download "L1234567890abcdef1234567890abcdef"

# 下载 Z-Library 书籍（需要哈希）
ebooks-download "123456" --hash "abcdef" -p zlibrary

# 保存到指定目录
ebooks-download "book-url" -s "./my-books/"
```

## 配置

### 配置文件 (JSON)
```json
{
  "enable_archive": true,
  "enable_liber3": true,
  "enable_calibre": false,
  "calibre_web_url": "http://localhost:8083",
  "enable_zlib": false,
  "zlib_email": "",
  "zlib_password": "",
  "enable_annas": false,
  "max_results": 20,
  "timeout": 30,
  "proxy": null
}
```

### 环境变量
```bash
export EBOOKS_CALIBRE_URL="http://localhost:8083"
export EBOOKS_ZLIB_EMAIL="your_email@example.com"
export EBOOKS_ZLIB_PASSWORD="your_password"
export EBOOKS_PROXY="http://proxy:8080"
```

## API 参考

### EbooksLibrary

电子书操作的主要类。

#### 方法

- `search(query, platforms=None, limit=None)` - 搜索电子书
- `download(download_info, save_path=None, return_content=False)` - 下载电子书
- `get_book_info(download_info)` - 获取详细书籍信息
- `test_platform_connection(platform)` - 测试平台连接
- `get_enabled_platforms()` - 获取已启用平台列表
- `close()` - 关闭库并清理资源

### 数据模型

#### BookInfo
```python
@dataclass
class BookInfo:
    title: str                              # 标题
    authors: Optional[str] = None           # 作者
    year: Optional[str] = None              # 年份
    publisher: Optional[str] = None         # 出版社
    language: Optional[str] = None          # 语言
    description: Optional[str] = None       # 描述
    cover_url: Optional[str] = None         # 封面链接
    file_size: Optional[str] = None         # 文件大小
    file_type: Optional[str] = None         # 文件类型
    isbn: Optional[str] = None              # ISBN
```

#### DownloadInfo
```python
@dataclass
class DownloadInfo:
    platform: Platform                             # 平台
    download_url: Optional[str] = None             # 下载链接
    book_id: Optional[str] = None                  # 书籍ID
    hash_id: Optional[str] = None                  # 哈希ID
    file_name: Optional[str] = None                # 文件名
    requires_auth: bool = False                    # 是否需要认证
    additional_params: Optional[Dict[str, Any]] = None  # 额外参数
```

#### SearchResult
```python
@dataclass
class SearchResult:
    book_info: BookInfo                     # 书籍信息
    download_info: DownloadInfo             # 下载信息
    platform: Platform                     # 平台
    relevance_score: Optional[float] = None # 相关性评分
```

## 示例

查看 `examples/` 目录获取完整的使用示例：

- `basic_usage.py` - 基础搜索和下载示例
- `advanced_usage.py` - 高级配置和批量操作

## 平台特定说明

### Calibre-Web
- 需要运行 Calibre-Web 服务器
- 在配置中设置 `calibre_web_url`
- 支持 OPDS 目录搜索和下载

### Z-Library
- 需要有效的账户凭据
- 下载有速率限制
- 支持多种条件搜索

### Archive.org
- 无需认证
- 拥有大量公共领域书籍
- 支持 PDF 和 EPUB 格式

### Liber3
- 无需认证
- 使用 IPFS 进行文件分发
- 技术类书籍选择丰富

### Anna's Archive
- 不提供直接下载
- 提供其他平台的链接
- 拥有全面的书籍数据库

## 错误处理

库提供了特定的异常类型：

```python
from ebooks_library.exceptions import (
    EbooksLibraryError,      # 基础异常
    SearchError,             # 搜索相关错误
    DownloadError,           # 下载相关错误
    AuthenticationError,     # 认证失败
    NetworkError,            # 网络问题
    ConfigurationError       # 配置问题
)

try:
    results = await library.search("查询")
except SearchError as e:
    print(f"搜索失败: {e}")
except NetworkError as e:
    print(f"网络错误: {e}")
```

## 开发

### 运行测试
```bash
pytest
```

### 代码格式化
```bash
black ebooks_library/
```

### 类型检查
```bash
mypy ebooks_library/
```

## 贡献

1. Fork 仓库
2. 创建功能分支
3. 进行更改
4. 如适用，添加测试
5. 运行测试和代码检查
6. 提交 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详情请见 LICENSE 文件。

## 免责声明

此库仅供教育和个人使用。请尊重各平台的服务条款和适用的版权法律。作者不对此库的任何滥用负责。

## 更新日志

### 版本 1.0.0
- 初始发布
- 支持 5 个电子书平台
- 异步 API
- CLI 工具
- 完整的文档和示例