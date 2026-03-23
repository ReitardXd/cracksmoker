import sys
import os
import shutil
import subprocess
import platform

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_SCRIPT = os.path.join(SCRIPT_DIR, "cracksmoker.py")

# ==============================================================================
# HELPERS
# ==============================================================================

def banner():
    print("\n\033[91m  CRACKSMOKER // SETUP\033[0m")
    print("\033[90m  ──────────────────────\033[0m\n")

def ok(msg):    print(f"\033[92m  ✓  {msg}\033[0m")
def info(msg):  print(f"\033[96m  →  {msg}\033[0m")
def warn(msg):  print(f"\033[93m  ⚠  {msg}\033[0m")
def err(msg):   print(f"\033[91m  ✗  {msg}\033[0m")

def run(cmd, check=True):
    info(f"running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        err(result.stderr.strip() or f"command failed (exit {result.returncode})")
        sys.exit(1)
    return result

# ==============================================================================
# OS DETECTION
# ==============================================================================

def detect():
    system = platform.system()
    if system == "Windows":
        return "windows"
    if system == "Darwin":
        return "macos"
    if system == "Linux":
        # try to figure out distro
        try:
            with open("/etc/os-release") as f:
                data = f.read().lower()
            if any(d in data for d in ("ubuntu", "debian", "kali", "mint", "pop")):
                return "debian"
            if any(d in data for d in ("fedora", "rhel", "centos", "rocky")):
                return "fedora"
            if "arch" in data or "manjaro" in data:
                return "arch"
        except FileNotFoundError:
            pass
        return "linux_generic"
    return "unknown"

# ==============================================================================
# HASHCAT INSTALL
# ==============================================================================

def install_hashcat(os_type):
    info(f"detected OS: {os_type}")
    info("attempting to install hashcat...\n")

    if os_type == "debian":
        run(["sudo", "apt-get", "update", "-qq"])
        run(["sudo", "apt-get", "install", "-y", "hashcat"])

    elif os_type == "fedora":
        run(["sudo", "dnf", "install", "-y", "hashcat"])

    elif os_type == "arch":
        run(["sudo", "pacman", "-Sy", "--noconfirm", "hashcat"])

    elif os_type == "macos":
        if not shutil.which("brew"):
            err("Homebrew not found. Install it first: https://brew.sh")
            sys.exit(1)
        run(["brew", "install", "hashcat"])

    elif os_type == "windows":
        # Try winget first, fall back to instructions
        if shutil.which("winget"):
            result = run(["winget", "install", "--id", "Hashcat.Hashcat", "-e"], check=False)
            if result.returncode != 0:
                _windows_manual()
        else:
            _windows_manual()

    else:
        warn("couldn't auto-install for your distro.")
        print("\n  Install hashcat manually:")
        print("    https://hashcat.net/hashcat/")
        print("  Then re-run this script.\n")
        sys.exit(1)

def _windows_manual():
    warn("couldn't auto-install hashcat on Windows.")
    print("\n  Do it manually:")
    print("  1. Download from https://hashcat.net/hashcat/")
    print("  2. Extract and add the folder to your PATH")
    print("  3. Re-run this script\n")
    sys.exit(1)

# ==============================================================================
# DEPENDENCY CHECK
# ==============================================================================

def check_python():
    major, minor = sys.version_info[:2]
    if major < 3 or (major == 3 and minor < 8):
        err(f"Python 3.8+ required (you have {major}.{minor})")
        sys.exit(1)
    ok(f"Python {major}.{minor}")

def check_hashcat():
    path = shutil.which("hashcat")
    if path:
        result = subprocess.run(["hashcat", "--version"], capture_output=True, text=True)
        version = result.stdout.strip()
        ok(f"hashcat found: {path}  ({version})")
        return True
    return False

def check_main_script():
    if not os.path.exists(MAIN_SCRIPT):
        err(f"cracksmoker.py not found at: {MAIN_SCRIPT}")
        err("make sure setup.py and cracksmoker.py are in the same directory")
        sys.exit(1)
    ok("cracksmoker.py found")

def check_tkinter():
    try:
        import tkinter
        ok("tkinter available")
    except ImportError:
        warn("tkinter not found — trying to install...")
        os_type = detect()
        if os_type == "debian":
            run(["sudo", "apt-get", "install", "-y", "python3-tk"])
        elif os_type == "fedora":
            run(["sudo", "dnf", "install", "-y", "python3-tkinter"])
        elif os_type == "arch":
            run(["sudo", "pacman", "-Sy", "--noconfirm", "tk"])
        elif os_type == "macos":
            warn("on macOS, reinstall Python from python.org (includes tkinter)")
            sys.exit(1)
        else:
            err("please install python3-tk for your distro")
            sys.exit(1)

# ==============================================================================
# LAUNCH
# ==============================================================================

def launch():
    info(f"launching cracksmoker.py...")
    print()
    try:
        subprocess.Popen([sys.executable, MAIN_SCRIPT])
    except Exception as e:
        err(f"failed to launch: {e}")
        sys.exit(1)

# ==============================================================================
# MAIN
# ==============================================================================

def main():
    banner()

    check_python()
    check_tkinter()
    check_main_script()

    if not check_hashcat():
        warn("hashcat not found — installing now\n")
        os_type = detect()
        install_hashcat(os_type)

        # Verify install worked
        if not check_hashcat():
            err("hashcat install failed or not in PATH after install")
            err("try installing manually: https://hashcat.net/hashcat/")
            sys.exit(1)

    print()
    launch()
    ok("done — cracksmoker is running\n")

if __name__ == "__main__":
    main()
