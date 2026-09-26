import os
import subprocess
import sys

def main():
    project_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("Installing requirements...")
    try:
        subprocess.check_call(["pip", "install", "-r", "requirements.txt"], shell=True)
    except Exception as e:
        print(f"Warning: Failed to run pip install. Assuming dependencies are met. ({e})")
    
    print("Installing Playwright browsers...")
    try:
        subprocess.check_call(["playwright", "install", "chromium"], shell=True)
    except Exception as e:
        print(f"Warning: Failed to install playwright browsers. ({e})")
    
    print("Running PyInstaller...")
    
    add_data_js = "src/guardian/extraction/dom_extract.js;guardian/extraction"
    add_data_rules = "src/guardian/resources/rules/*;guardian/resources/rules"
    
    pyinstaller_cmd = [
        "pyinstaller",
        "--name", "CleanGuardian",
        "--windowed",
        "--noconfirm",
        "--collect-all", "playwright",
        "--collect-all", "pyahocorasick",
        "--add-data", add_data_js,
        "--add-data", add_data_rules,
        "src/guardian/__main__.py"
    ]
    
    subprocess.check_call(pyinstaller_cmd, cwd=project_dir)
    print("Build complete! Check the 'dist' folder.")

if __name__ == "__main__":
    main()
