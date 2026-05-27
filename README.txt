Markdown2PDF Converter v1.0
================================

SYSTEM REQUIREMENTS:
- Windows 7/8/10/11 (64-bit)
- Internet connection (for first-time setup)
- Administrator privileges (for installing dependencies)

FIRST TIME USE:
1. Double-click "Markdown2PDF.exe"
2. If dependencies are missing, click "Auto Install"
3. Wait for installation to complete (5-10 minutes)
4. Select your .md file and click "Convert"

FEATURES:
- Math formulas (14pt)
- Full-width horizontal rules
- Gray quote blocks with left border
- Bold Chinese titles (SimHei)
- Auto-fix special characters (①→(1))
- Auto-fix Obsidian wiki links [[...]]
- Page headers with chapter name and page number

TROUBLESHOOTING:
Q: Program says "Dependencies missing"
A: Click "Auto Install" button and wait

Q: Installation fails
A: Please install manually:
   1. Pandoc: https://pandoc.org/installing.html
   2. MiKTeX: https://miktex.org/download
   
   During MiKTeX installation, select:
   - "Install missing packages on the fly"
   - "Add to PATH"

Q: First conversion is very slow
A: MiKTeX needs to download fonts and packages.
   Keep internet connected.

Q: Chinese characters not displaying
A: Ensure Windows has SimSun and SimHei fonts installed

NOTE:
- Dependencies only need to be installed once
- PDF is saved in the same folder as the input file
- Program creates temporary files during conversion
