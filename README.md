# Markdown to PDF Converter

一款功能强大的 Markdown 转 PDF 工具，提供图形界面和命令行两种使用方式，专为中文文档优化。

## ✨ 特性

- **数学公式支持** — 完美渲染 LaTeX 数学公式（14pt 字号）
- **中文优化** — 使用 SimHei（黑体）作为标题字体，SimSun（宋体）作为正文字体
- **全宽分割线** — 自动将 Markdown 分割线转换为页面全宽样式
- **优雅引用块** — 灰色背景带左侧边框的引用样式
- **自动字符修复** — 将特殊符号（如 ①、② 等）转换为兼容格式（(1)、(2) 等）
- **Obsidian 链接修复** — 自动移除 `[[...]]` 格式的 Wiki 链接标记
- **智能页眉** — 显示章节名称和页码
- **依赖自动安装** — 首次使用时自动下载并安装 Pandoc 和 MiKTeX

## 📦 包含文件

| 文件 | 说明 |
|------|------|
| `Markdown-to-Pdf.exe` | Windows 可执行文件（GUI 版本） |
| `Markdown-to-Pdf.py` | Python 源代码（GUI 版本） |
| `Markdown-to-Pdf.ps1` | PowerShell 脚本（CLI 版本） |

## 🚀 使用方法

### GUI 版本（推荐）

1. 双击运行 `Markdown-to-Pdf.exe`
2. 如提示缺少依赖，点击 **"Auto Install"** 按钮自动安装
3. 等待安装完成（约 5-10 分钟）
4. 选择要转换的 `.md` 文件，点击 **"Convert"**

### CLI 版本

```powershell
# 基础用法
.\Markdown-to-Pdf.ps1 -InputFile "文档.md"

# 指定输出文件
.\Markdown-to-Pdf.ps1 -InputFile "文档.md" -OutputFile "输出.pdf"
```

## 📋 系统要求

- Windows 7/8/10/11 (64-bit)
- 互联网连接（首次安装依赖时需要）
- 管理员权限（安装依赖时需要）

## 🔧 依赖项

工具依赖以下软件，首次运行时会自动检测并提示安装：

- **[Pandoc](https://pandoc.org/)** — Markdown 到 LaTeX 的转换
- **[MiKTeX](https://miktex.org/)** — LaTeX 引擎，用于生成 PDF

### 手动安装

如自动安装失败，可手动下载安装：

1. 安装 Pandoc：https://pandoc.org/installing.html
2. 安装 MiKTeX：https://miktex.org/download
   - 安装时请选择 **"Install missing packages on the fly"**
   - 勾选 **"Add to PATH"**

## ⚙️ PDF 样式配置

生成的 PDF 具有以下样式特点：

- **页面**：A4 纸张，页边距 2.5cm
- **行距**：1.6 倍行距
- **代码块**：浅灰色背景，等宽字体
- **标题**：大号粗体黑体
- **页眉**：左侧显示章节名，右侧显示页码

## 🛠️ 技术栈

- **Python 3** + tkinter — GUI 界面
- **Pandoc** — Markdown 解析与 LaTeX 生成
- **MiKTeX / XeLaTeX** — PDF 编译
- **xeCJK** — 中文排版支持

## 📝 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！
