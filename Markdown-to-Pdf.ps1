param(
    [Parameter(Mandatory=$true)]
    [string]$InputFile,
    
    [string]$OutputFile = ""
)

# 如果没有指定输出文件，自动生成
if ([string]::IsNullOrEmpty($OutputFile)) {
    $OutputFile = [System.IO.Path]::ChangeExtension($InputFile, ".pdf")
}

# 确保输出目录存在
$outputDir = [System.IO.Path]::GetDirectoryName($OutputFile)
if ([string]::IsNullOrEmpty($outputDir)) {
    $outputDir = [System.IO.Path]::GetDirectoryName([System.IO.Path]::GetFullPath($InputFile))
    $OutputFile = [System.IO.Path]::Combine($outputDir, $OutputFile)
}

if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Markdown to PDF Converter" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "输入文件: $InputFile" -ForegroundColor Gray
Write-Host "输出文件: $OutputFile" -ForegroundColor Gray
Write-Host ""

# 1. 读取并修复特殊字符
Write-Host "[1/5] 修复特殊字符..." -ForegroundColor Yellow
$mdContent = Get-Content $InputFile -Raw -Encoding UTF8
$mdContent = $mdContent -replace '①', '(1)' `
                        -replace '②', '(2)' `
                        -replace '③', '(3)' `
                        -replace '④', '(4)' `
                        -replace '⑤', '(5)' `
                        -replace '⑥', '(6)' `
                        -replace '⑦', '(7)' `
                        -replace '⑧', '(8)' `
                        -replace '⑨', '(9)'

# 修复 Obsidian wiki 链接 [[#标题]] → 标题
$mdContent = $mdContent -replace '\[\[(.*?)\]\]', '$1'

# 清理文档开头的孤立符号（如 ]、[、]]、[[ 等）
$lines = $mdContent -split "`r?`n"
$cleanedLines = @()
$skipEmpty = $true
foreach ($line in $lines) {
    $stripped = $line.Trim()
    # 跳过开头的孤立 ]、[、]]、[[ 等
    if ($skipEmpty -and ($stripped -eq '' -or $stripped -eq ']' -or $stripped -eq '[' -or $stripped -eq ']]' -or $stripped -eq '[[')) {
        continue
    }
    $skipEmpty = $false
    $cleanedLines += $line
}
$mdContent = $cleanedLines -join "`n"

$tempDir = $env:TEMP
$fixedMd = Join-Path $tempDir "md2pdf_fixed.md"
$mdContent | Set-Content $fixedMd -Encoding UTF8
Write-Host "✓ 特殊字符修复完成" -ForegroundColor Green

# 2. 创建 header 文件
Write-Host "[2/5] 创建 LaTeX 配置文件..." -ForegroundColor Yellow
$headerFile = Join-Path $tempDir "header_14pt.tex"

$headerContent = @"
\usepackage{geometry}
\geometry{a4paper, margin=2.5cm}
\usepackage{xeCJK}
\setCJKmainfont{SimSun}
\setCJKsansfont{SimHei}
\setCJKmonofont{FangSong}
\usepackage{setspace}
\setstretch{1.6}
\usepackage{enumitem}
\setlist{nosep}
\usepackage{booktabs}
\usepackage{fancyhdr}
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\small\leftmark}
\fancyhead[R]{\small\thepage}
\renewcommand{\headrulewidth}{0.4pt}
\renewcommand{\footrulewidth}{0pt}
\usepackage{mdframed}
\newmdenv[
  leftmargin=0pt, rightmargin=0pt,
  innerleftmargin=12pt, innerrightmargin=12pt,
  innertopmargin=8pt, innerbottommargin=8pt,
  linewidth=3pt, linecolor=gray!50,
  backgroundcolor=gray!6,
  topline=false, rightline=false, bottomline=false,
  skipabove=8pt, skipbelow=8pt
]{myquote}
\renewenvironment{quote}
  {\begin{myquote}\small}
  {\end{myquote}}
\usepackage{amsmath}
\everymath{\displaystyle}
\DeclareMathSizes{11}{14}{11}{9}
\usepackage{titlesec}
\titleformat{\section}{\Large\bfseries\CJKfamily{zhhei}}{\thesection}{1em}{}
\titleformat{\subsection}{\large\bfseries\CJKfamily{zhhei}}{\thesubsection}{1em}{}
\titleformat{\subsubsection}{\normalsize\bfseries\CJKfamily{zhhei}}{\thesubsubsection}{1em}{}
\usepackage{listings}
\lstset{
  basicstyle=\ttfamily\small,
  backgroundcolor=\color{gray!10},
  frame=single, framerule=0pt, breaklines=true
}
\usepackage{hyperref}
\hypersetup{colorlinks=false}
"@

$headerContent | Out-File -Encoding utf8 $headerFile
Write-Host "✓ 配置文件创建完成" -ForegroundColor Green

# 3. 生成 tex 文件
Write-Host "[3/5] 生成 LaTeX 文件..." -ForegroundColor Yellow
$texPath = Join-Path $tempDir "md2pdf_temp.tex"

$pandocArgs = @(
    $fixedMd,
    "-o", $texPath,
    "-V", "documentclass=ctexart",
    "-V", "classoption=fontset=windows",
    "--include-in-header", $headerFile
)

$pandocResult = Start-Process -FilePath "pandoc" -ArgumentList $pandocArgs -Wait -PassThru -NoNewWindow
if ($pandocResult.ExitCode -ne 0) {
    Write-Host "✗ Pandoc 转换失败" -ForegroundColor Red
    exit 1
}
Write-Host "✓ LaTeX 文件生成完成" -ForegroundColor Green

# 4. 修复分割线为全宽
Write-Host "[4/5] 修复分割线..." -ForegroundColor Yellow

# 读取 tex 文件
$texContent = Get-Content $texPath -Raw -Encoding UTF8

# 替换 pandoc 生成的默认分割线
$oldPattern = '\begin{center}\rule{0.5\linewidth}{0.5pt}\end{center}'
$newPattern = '\vspace{0.5em}\noindent\rule{\linewidth}{0.5pt}\vspace{0.5em}'

$texContent = $texContent.Replace($oldPattern, $newPattern)

# 保存修复后的 tex
$texContent | Set-Content $texPath -Encoding UTF8

# 检查是否还有未替换的分割线
if ($texContent.Contains('\begin{center}\rule{')) {
    Write-Host "⚠ 警告: 仍有部分分割线未修复" -ForegroundColor Yellow
} else {
    Write-Host "✓ 分割线修复完成" -ForegroundColor Green
}

# 5. 编译 PDF
Write-Host "[5/5] 编译 PDF..." -ForegroundColor Yellow
$xelatex = "C:\Users\13818\AppData\Local\Programs\MiKTeX\miktex\bin\x64\xelatex.exe"

if (-not (Test-Path $xelatex)) {
    Write-Host "✗ 错误: 未找到 xelatex" -ForegroundColor Red
    Write-Host "  请确保 MiKTeX 已正确安装" -ForegroundColor Red
    exit 1
}

# 第1次编译
Write-Host "  第1次编译..." -ForegroundColor Gray
& $xelatex -interaction=nonstopmode -output-directory="$outputDir" "$texPath" 2>$null | Out-Null

# 第2次编译（修正页眉和交叉引用）
Write-Host "  第2次编译..." -ForegroundColor Gray
& $xelatex -interaction=nonstopmode -output-directory="$outputDir" "$texPath" 2>$null | Out-Null

# 6. 移动输出文件
$tempPdf = Join-Path $outputDir "md2pdf_temp.pdf"
if (Test-Path $tempPdf) {
    if (Test-Path $OutputFile) {
        Remove-Item $OutputFile -Force
    }
    Move-Item $tempPdf $OutputFile -Force
    
    $fileSize = (Get-Item $OutputFile).Length / 1MB
    Write-Host ""
    Write-Host "✅ 转换成功！" -ForegroundColor Green
    Write-Host "📄 输出: $OutputFile" -ForegroundColor Green
    Write-Host "📊 大小: $([math]::Round($fileSize, 2)) MB" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "✗ 转换失败，PDF 文件未生成" -ForegroundColor Red
}

# 清理临时文件
Remove-Item $fixedMd -ErrorAction SilentlyContinue
Remove-Item $texPath -ErrorAction SilentlyContinue
Remove-Item (Join-Path $outputDir "md2pdf_temp.log") -ErrorAction SilentlyContinue
Remove-Item (Join-Path $outputDir "md2pdf_temp.aux") -ErrorAction SilentlyContinue

Write-Host ""
