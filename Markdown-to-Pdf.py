import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess
import os
import sys
import re
import tempfile
import threading
import urllib.request
import shutil
from pathlib import Path

class DependencyManager:
    """Manage Pandoc and MiKTeX dependencies"""
    
    @staticmethod
    def find_in_path(cmd):
        """Find command in system PATH"""
        try:
            result = subprocess.run([cmd, "--version"], 
                                  capture_output=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    @staticmethod
    def find_xelatex():
        """Find xelatex executable"""
        import glob
        
        # Search common installation paths
        search_paths = []
        
        # User-specific paths
        user_profile = os.environ.get('USERPROFILE', '')
        if user_profile:
            search_paths.extend([
                os.path.join(user_profile, r"AppData\Local\Programs\MiKTeX\miktex\bin\x64\xelatex.exe"),
                os.path.join(user_profile, r"AppData\Local\MiKTeX\miktex\bin\x64\xelatex.exe"),
                os.path.join(user_profile, r"AppData\Roaming\MiKTeX\miktex\bin\x64\xelatex.exe"),
            ])
        
        # System-wide paths
        search_paths.extend([
            r"C:\Program Files\MiKTeX\miktex\bin\x64\xelatex.exe",
            r"C:\Program Files (x86)\MiKTeX\miktex\bin\x64\xelatex.exe",
            r"C:\MiKTeX\miktex\bin\x64\xelatex.exe",
        ])
        
        # Also try to glob search in Program Files
        program_files = os.environ.get('ProgramFiles', r"C:\Program Files")
        program_files_x86 = os.environ.get('ProgramFiles(x86)', r"C:\Program Files (x86)")
        
        for pf in [program_files, program_files_x86]:
            if pf and os.path.exists(pf):
                pattern = os.path.join(pf, "MiKTeX*", "miktex", "bin", "x64", "xelatex.exe")
                matches = glob.glob(pattern)
                if matches:
                    search_paths.extend(matches)
        
        # User AppData search
        if user_profile:
            for appdata in ["Local", "Roaming"]:
                appdata_path = os.path.join(user_profile, "AppData", appdata)
                if os.path.exists(appdata_path):
                    pattern = os.path.join(appdata_path, "Programs", "MiKTeX*", "miktex", "bin", "x64", "xelatex.exe")
                    matches = glob.glob(pattern)
                    if matches:
                        search_paths.extend(matches)
                    # Also search directly under MiKTeX
                    pattern2 = os.path.join(appdata_path, "MiKTeX*", "miktex", "bin", "x64", "xelatex.exe")
                    matches2 = glob.glob(pattern2)
                    if matches2:
                        search_paths.extend(matches2)
        
        for path in search_paths:
            if path and os.path.exists(path):
                return path
        
        # Try PATH as fallback
        if DependencyManager.find_in_path("xelatex"):
            # Try to get full path
            try:
                result = subprocess.run(["where", "xelatex"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    full_path = result.stdout.strip().split('\n')[0].strip()
                    if os.path.exists(full_path):
                        return full_path
            except:
                pass
            return "xelatex"
        
        return None
    
    @staticmethod
    def find_pandoc():
        """Find pandoc executable"""
        if DependencyManager.find_in_path("pandoc"):
            return "pandoc"
        return None
    
    @staticmethod
    def refresh_path_env():
        """Refresh PATH environment variable from Windows registry"""
        try:
            import winreg
            # Open the system environment key
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment") as key:
                try:
                    sys_path, _ = winreg.QueryValueEx(key, "Path")
                except FileNotFoundError:
                    sys_path = ""
            
            # Open the user environment key
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as key:
                try:
                    user_path, _ = winreg.QueryValueEx(key, "Path")
                except FileNotFoundError:
                    user_path = ""
            
            # Combine and update current process PATH
            new_path = sys_path
            if user_path:
                new_path = user_path + ";" + sys_path if sys_path else user_path
            
            os.environ['PATH'] = new_path
            return True
        except Exception as e:
            print(f"Failed to refresh PATH: {e}")
            return False
    
    @staticmethod
    def install_pandoc_silent(progress_callback=None):
        """Silently install Pandoc"""
        try:
            if progress_callback:
                progress_callback("Downloading Pandoc...")
            
            # Download Pandoc installer
            url = "https://github.com/jgm/pandoc/releases/download/3.1.11/pandoc-3.1.11-windows-x86_64.msi"
            installer = os.path.join(tempfile.gettempdir(), "pandoc_install.msi")
            
            urllib.request.urlretrieve(url, installer)
            
            if progress_callback:
                progress_callback("Installing Pandoc...")
            
            # Silent install
            subprocess.run(["msiexec", "/i", installer, "/quiet", "/norestart"], 
                         check=True, timeout=120)
            
            os.remove(installer)
            
            # Refresh PATH to detect newly installed Pandoc
            DependencyManager.refresh_path_env()
            
            return True
        except Exception as e:
            print(f"Pandoc install error: {e}")
            return False
    
    @staticmethod
    def install_miktex_silent(progress_callback=None):
        """Silently install MiKTeX"""
        try:
            if progress_callback:
                progress_callback("Downloading MiKTeX...")
            
            # Download MiKTeX basic installer
            url = "https://miktex.org/download/ctan/systems/win32/miktex/setup/windows-x64/basic-miktex-23.10-x64.exe"
            installer = os.path.join(tempfile.gettempdir(), "miktex_install.exe")
            
            urllib.request.urlretrieve(url, installer)
            
            if progress_callback:
                progress_callback("Installing MiKTeX (this may take 5-10 minutes)...")
            
            # Silent install
            subprocess.run([installer, "--auto-install=yes", "--unattended"], 
                         check=True, timeout=600)
            
            os.remove(installer)
            
            # Refresh PATH to detect newly installed MiKTeX
            DependencyManager.refresh_path_env()
            
            # Configure MiKTeX to auto-install packages without prompting
            if progress_callback:
                progress_callback("Configuring MiKTeX...")
            
            xelatex_path = DependencyManager.find_xelatex()
            if xelatex_path and xelatex_path != "xelatex":
                miktex_bin = os.path.dirname(xelatex_path)
                initexmf = os.path.join(miktex_bin, "initexmf.exe")
                if os.path.exists(initexmf):
                    try:
                        subprocess.run([initexmf, "--set-config-value=[MPM]AutoInstall=1"], 
                                     capture_output=True, timeout=30)
                    except:
                        pass
            
            return True
        except Exception as e:
            print(f"MiKTeX install error: {e}")
            return False

class MD2PDFConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("Markdown to PDF Converter v1.0")
        self.root.geometry("700x550")
        self.root.resizable(True, True)
        
        self.style = ttk.Style()
        self.style.configure("Title.TLabel", font=("Microsoft YaHei", 16, "bold"))
        self.style.configure("Subtitle.TLabel", font=("Microsoft YaHei", 10))
        self.style.configure("Action.TButton", font=("Microsoft YaHei", 11))
        
        self.temp_dir = tempfile.gettempdir()
        self.xelatex_path = None
        self.pandoc_path = None
        
        self.setup_ui()
        self.check_deps_async()
        
    def setup_ui(self):
        # Title
        title_frame = ttk.Frame(self.root, padding="20")
        title_frame.pack(fill=tk.X)
        
        ttk.Label(title_frame, text="Markdown to PDF Converter", style="Title.TLabel").pack()
        ttk.Label(title_frame, text="Math formulas | Full-width dividers | Gray quotes", style="Subtitle.TLabel").pack()
        
        # Dependency status
        self.deps_frame = ttk.LabelFrame(self.root, text="Dependencies", padding="10")
        self.deps_frame.pack(fill=tk.X, padx=20, pady=5)
        
        self.pandoc_var = tk.StringVar(value="Checking...")
        self.miktex_var = tk.StringVar(value="Checking...")
        
        ttk.Label(self.deps_frame, text="Pandoc:").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(self.deps_frame, textvariable=self.pandoc_var, foreground="blue").grid(row=0, column=1, sticky=tk.W, padx=5)
        
        ttk.Label(self.deps_frame, text="MiKTeX:").grid(row=1, column=0, sticky=tk.W)
        ttk.Label(self.deps_frame, textvariable=self.miktex_var, foreground="blue").grid(row=1, column=1, sticky=tk.W, padx=5)
        
        self.install_btn = ttk.Button(self.deps_frame, text="Auto Install", command=self.install_deps_async)
        self.install_btn.grid(row=0, column=2, rowspan=2, padx=10)
        self.install_btn.config(state='disabled')
        
        # File selection
        file_frame = ttk.LabelFrame(self.root, text="Files", padding="15")
        file_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Input
        input_frame = ttk.Frame(file_frame)
        input_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(input_frame, text="Input:").pack(side=tk.LEFT)
        self.input_var = tk.StringVar()
        self.input_entry = ttk.Entry(input_frame, textvariable=self.input_var, width=50)
        self.input_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(input_frame, text="Browse...", command=self.browse_input).pack(side=tk.LEFT)
        
        # Output
        output_frame = ttk.Frame(file_frame)
        output_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(output_frame, text="Output:").pack(side=tk.LEFT)
        self.output_var = tk.StringVar()
        self.output_entry = ttk.Entry(output_frame, textvariable=self.output_var, width=50)
        self.output_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(output_frame, text="Browse...", command=self.browse_output).pack(side=tk.LEFT)
        
        # Convert button
        button_frame = ttk.Frame(self.root, padding="10")
        button_frame.pack(fill=tk.X)
        
        self.convert_btn = ttk.Button(
            button_frame, 
            text="Convert", 
            command=self.start_conversion,
            style="Action.TButton"
        )
        self.convert_btn.pack(pady=10)
        self.convert_btn.config(state='disabled')
        
        # Progress
        self.progress = ttk.Progressbar(self.root, mode='determinate', length=600)
        self.progress.pack(padx=20, pady=5)
        
        self.status_var = tk.StringVar(value="Checking dependencies...")
        self.status_label = ttk.Label(self.root, textvariable=self.status_var, font=("Microsoft YaHei", 10))
        self.status_label.pack(pady=5)
        
        # Log
        log_frame = ttk.LabelFrame(self.root, text="Log", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame, 
            wrap=tk.WORD, 
            height=8,
            font=("Consolas", 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def check_deps_async(self):
        """Check dependencies in background"""
        def check():
            self.pandoc_path = DependencyManager.find_pandoc()
            self.xelatex_path = DependencyManager.find_xelatex()
            
            self.root.after(0, self.update_dep_status)
        
        threading.Thread(target=check, daemon=True).start()
    
    def update_dep_status(self):
        """Update dependency status UI"""
        if self.pandoc_path:
            self.pandoc_var.set("Installed")
            self.deps_frame.grid_slaves(row=0, column=1)[0].config(foreground="green")
        else:
            self.pandoc_var.set("Not found")
            self.deps_frame.grid_slaves(row=0, column=1)[0].config(foreground="red")
        
        if self.xelatex_path:
            self.miktex_var.set("Installed")
            self.deps_frame.grid_slaves(row=1, column=1)[0].config(foreground="green")
        else:
            self.miktex_var.set("Not found")
            self.deps_frame.grid_slaves(row=1, column=1)[0].config(foreground="red")
        
        if self.pandoc_path and self.xelatex_path:
            self.status_var.set("Ready")
            self.convert_btn.config(state='normal')
            self.install_btn.config(state='disabled')
        else:
            self.status_var.set("Dependencies missing - Click Auto Install")
            self.convert_btn.config(state='disabled')
            self.install_btn.config(state='normal')
    
    def install_deps_async(self):
        """Install dependencies in background"""
        self.install_btn.config(state='disabled')
        self.status_var.set("Installing dependencies...")
        
        def install():
            success = True
            
            # Install Pandoc
            if not self.pandoc_path:
                self.root.after(0, lambda: self.log("Installing Pandoc..."))
                if DependencyManager.install_pandoc_silent(
                    lambda msg: self.root.after(0, lambda: self.status_var.set(msg))
                ):
                    self.pandoc_path = DependencyManager.find_pandoc()
                    self.root.after(0, lambda: self.log("Pandoc installed"))
                else:
                    self.root.after(0, lambda: self.log("Pandoc install failed"))
                    success = False
            
            # Install MiKTeX
            if not self.xelatex_path:
                self.root.after(0, lambda: self.log("Installing MiKTeX..."))
                if DependencyManager.install_miktex_silent(
                    lambda msg: self.root.after(0, lambda: self.status_var.set(msg))
                ):
                    self.xelatex_path = DependencyManager.find_xelatex()
                    self.root.after(0, lambda: self.log("MiKTeX installed"))
                else:
                    self.root.after(0, lambda: self.log("MiKTeX install failed"))
                    success = False
            
            self.root.after(0, lambda: self.install_complete(success))
        
        threading.Thread(target=install, daemon=True).start()
    
    def install_complete(self, success):
        """Called when installation completes"""
        if success:
            # Refresh PATH and re-check dependencies
            DependencyManager.refresh_path_env()
            self.pandoc_path = DependencyManager.find_pandoc()
            self.xelatex_path = DependencyManager.find_xelatex()
            self.update_dep_status()
            messagebox.showinfo("Success", "Dependencies installed!\nYou can now convert files.")
        else:
            self.update_dep_status()
            messagebox.showerror("Error", "Some dependencies failed to install.\nPlease install manually:\n1. Pandoc: https://pandoc.org/installing.html\n2. MiKTeX: https://miktex.org/download")
    
    def browse_input(self):
        filename = filedialog.askopenfilename(
            title="Select Markdown file",
            filetypes=[("Markdown files", "*.md"), ("All files", "*.*")]
        )
        if filename:
            self.input_var.set(filename)
            output = os.path.splitext(filename)[0] + ".pdf"
            self.output_var.set(output)
            
    def browse_output(self):
        filename = filedialog.asksaveasfilename(
            title="Save PDF file",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")]
        )
        if filename:
            self.output_var.set(filename)
            
    def update_progress(self, value, status):
        self.progress['value'] = value
        self.status_var.set(status)
        self.root.update_idletasks()
        
    def create_header_file(self):
        header_content = r"""
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
"""
        header_path = os.path.join(self.temp_dir, "header_14pt.tex")
        with open(header_path, 'w', encoding='utf-8') as f:
            f.write(header_content)
        return header_path
        
    def fix_special_chars(self, content):
        replacements = {
            '①': '(1)', '②': '(2)', '③': '(3)', '④': '(4)',
            '⑤': '(5)', '⑥': '(6)', '⑦': '(7)', '⑧': '(8)', '⑨': '(9)'
        }
        for old, new in replacements.items():
            content = content.replace(old, new)
        
        content = re.sub(r'\[\[(.*?)\]\]', r'\1', content)
        
        lines = content.split('\n')
        cleaned_lines = []
        skip_empty = True
        for line in lines:
            stripped = line.strip()
            if skip_empty and (stripped == '' or stripped == ']' or stripped == '[' or stripped == ']]' or stripped == '[['):
                continue
            skip_empty = False
            cleaned_lines.append(line)
        content = '\n'.join(cleaned_lines)
        
        return content
        
    def fix_horizontal_rules(self, tex_content):
        pattern = r'\\begin\{center\}\\rule\{0\.5\\linewidth\}\{0\.5pt\}\\end\{center\}'
        replacement = r'\\vspace{0.5em}\\noindent\\rule{\\linewidth}{0.5pt}\\vspace{0.5em}'
        return re.sub(pattern, replacement, tex_content)
        
    def run_command(self, cmd, cwd=None):
        try:
            result = subprocess.run(
                cmd, 
                shell=True, 
                capture_output=True, 
                text=True, 
                cwd=cwd,
                timeout=300
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Timeout"
        except Exception as e:
            return False, "", str(e)
            
    def convert(self):
        input_file = self.input_var.get()
        output_file = self.output_var.get()
        
        if not input_file or not os.path.exists(input_file):
            messagebox.showerror("Error", "Please select a valid input file!")
            return
            
        if not output_file:
            output_file = os.path.splitext(input_file)[0] + ".pdf"
            
        self.convert_btn.config(state='disabled')
        self.progress['value'] = 0
        
        try:
            # Step 1
            self.update_progress(10, "Fixing special chars...")
            self.log("[1/5] Reading and fixing...")
            
            with open(input_file, 'r', encoding='utf-8') as f:
                md_content = f.read()
                
            md_content = self.fix_special_chars(md_content)
            
            fixed_md = os.path.join(self.temp_dir, "md2pdf_fixed.md")
            with open(fixed_md, 'w', encoding='utf-8') as f:
                f.write(md_content)
            self.log("Done")
            
            # Step 2
            self.update_progress(25, "Generating LaTeX...")
            self.log("[2/5] Generating LaTeX...")
            
            header_path = self.create_header_file()
            tex_path = os.path.join(self.temp_dir, "md2pdf_temp.tex")
            
            pandoc_cmd = f'"{self.pandoc_path or "pandoc"}" "{fixed_md}" -o "{tex_path}" -V documentclass=ctexart -V classoption=fontset=windows --include-in-header="{header_path}"'
            success, stdout, stderr = self.run_command(pandoc_cmd)
            
            if not success:
                self.log(f"Error: {stderr}")
                messagebox.showerror("Error", f"Pandoc failed:\n{stderr}")
                return
                
            self.log("Done")
            
            # Step 3
            self.update_progress(40, "Fixing dividers...")
            self.log("[3/5] Fixing horizontal rules...")
            
            with open(tex_path, 'r', encoding='utf-8') as f:
                tex_content = f.read()
                
            tex_content = self.fix_horizontal_rules(tex_content)
            
            with open(tex_path, 'w', encoding='utf-8') as f:
                f.write(tex_content)
                
            self.log("Done")
            
            # Step 4
            self.update_progress(60, "Compiling PDF (1/2)...")
            self.log("[4/5] Compiling PDF (pass 1)...")
            
            xelatex = self.xelatex_path or DependencyManager.find_xelatex() or "xelatex"
            output_dir = os.path.dirname(output_file)
            
            # Verify xelatex is actually available
            xelatex_exists = (xelatex != "xelatex" and os.path.exists(xelatex)) or shutil.which("xelatex")
            if not xelatex_exists:
                self.log("Error: xelatex not found")
                messagebox.showerror("Error", "xelatex not found!\nPlease install MiKTeX.")
                return
                
            cmd1 = f'"{xelatex}" -interaction=nonstopmode -output-directory="{output_dir}" "{tex_path}"'
            success, stdout, stderr = self.run_command(cmd1)
            
            if not success:
                self.log("Warning: Pass 1 had warnings")
            else:
                self.log("Done")
                
            # Step 5
            self.update_progress(80, "Compiling PDF (2/2)...")
            self.log("[5/5] Compiling PDF (pass 2)...")
            
            success, stdout, stderr = self.run_command(cmd1)
            
            if not success:
                self.log("Warning: Pass 2 had warnings")
            else:
                self.log("Done")
                
            # Move file
            temp_pdf = os.path.join(output_dir, "md2pdf_temp.pdf")
            if os.path.exists(temp_pdf):
                if os.path.exists(output_file):
                    os.remove(output_file)
                os.rename(temp_pdf, output_file)
                
            # Cleanup
            self.cleanup(output_dir)
            
            self.update_progress(100, "Done!")
            self.log("Success!")
            self.log(f"Output: {output_file}")
            
            if os.path.exists(output_file):
                size = os.path.getsize(output_file) / 1024 / 1024
                self.log(f"Size: {size:.2f} MB")
                messagebox.showinfo("Success", f"PDF created!\n\n{output_file}\nSize: {size:.2f} MB")
            else:
                messagebox.showerror("Error", "PDF not generated.")
                
        except Exception as e:
            self.log(f"Error: {str(e)}")
            messagebox.showerror("Error", f"Conversion error:\n{str(e)}")
            
        finally:
            self.convert_btn.config(state='normal')
            
    def cleanup(self, output_dir):
        files = [
            os.path.join(self.temp_dir, "md2pdf_fixed.md"),
            os.path.join(self.temp_dir, "md2pdf_temp.tex"),
            os.path.join(self.temp_dir, "header_14pt.tex"),
            os.path.join(output_dir, "md2pdf_temp.log"),
            os.path.join(output_dir, "md2pdf_temp.aux"),
            os.path.join(output_dir, "md2pdf_temp.out"),
        ]
        for f in files:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except:
                    pass
                     
    def start_conversion(self):
        thread = threading.Thread(target=self.convert)
        thread.daemon = True
        thread.start()

def main():
    root = tk.Tk()
    app = MD2PDFConverter(root)
    
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()

if __name__ == "__main__":
    main()
