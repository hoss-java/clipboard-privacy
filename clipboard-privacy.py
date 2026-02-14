#!/usr/bin/env python3
import json
import re
import subprocess
import platform
import os
import sys
import argparse
import socket
import getpass

#Define the name of the settings file and desired hotkey
SETTINGS_FILE = 'clipboard-privacy.json'
HOTKEY = "<Control><Alt>c"  # Desired hotkey combination
SCRIPT_FILE = os.path.abspath(__file__)
SCRIPT_PATH = os.path.dirname(SCRIPT_FILE)
FULL_COMMAND = f"python3 '{SCRIPT_FILE}'"

def load_settings(file_path):
    logging.info(file_path)
    with open(file_path, 'r') as f:
        settings = json.load(f)

    system_info_patterns = []

    system = platform.system()
    if system == "Linux":
        # Collect available system information patterns
            system_info_patterns.append({
                "pattern": r"\b{}\b".format(re.escape(getpass.getuser())),  # Current username
                "replacement": "username"
            })
            system_info_patterns.append({
                "pattern": r"\b{}\b".format(re.escape(socket.gethostname())),  # Hostname
                "replacement": "hostname"
            })
    elif system == "Windows":
        # include COMPUTERNAME env var if different from socket.gethostname()
        comp = (os.environ.get("COMPUTERNAME") or "").strip()
        if comp and comp != host:
            system_info_patterns.append({
                "pattern": r"\b{}\b".format(re.escape(comp)),
                "replacement": "hostname"
            })
        # optionally include userprofile or user domain info
        userdomain = (os.environ.get("USERDOMAIN") or "").strip()
        if userdomain:
            system_info_patterns.append({
                "pattern": r"\b{}\b".format(re.escape(userdomain)),
                "replacement": "userdomain"
            })
    elif system == "Darwin":
        # macOS: try to get the local hostname (ComputerName or LocalHostName)
        try:
            # scutil --get ComputerName or LocalHostName
            cn = subprocess.run(["scutil", "--get", "ComputerName"], capture_output=True, text=True, check=False).stdout.strip()
            if cn and cn != host:
                system_info_patterns.append({
                    "pattern": r"\b{}\b".format(re.escape(cn)),
                    "replacement": "hostname"
                })
        except Exception:
            pass

        try:
            lhn = subprocess.run(["scutil", "--get", "LocalHostName"], capture_output=True, text=True, check=False).stdout.strip()
            if lhn and lhn != host and lhn != cn:
                system_info_patterns.append({
                    "pattern": r"\b{}\b".format(re.escape(lhn)),
                    "replacement": "hostname"
                })
        except Exception:
            pass

    # Ensure settings has 'rules' key
    if "rules" not in settings or not isinstance(settings["rules"], list):
        settings["rules"] = []

    # Add system info rules to the existing rules
    settings['rules'].extend(system_info_patterns)

    return settings

# Check for available clipboard tools
def check_clipboard_tools():
    if platform.system() == "Windows":
        try:
            subprocess.run(["powershell", "Get-Clipboard"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return "powershell"
        except FileNotFoundError:
            print("PowerShell not found. Make sure it is installed.")
            return None
    elif platform.system() == "Darwin":
        try:
            subprocess.run(["pbpaste"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return "pbpaste"
        except FileNotFoundError:
            print("pbpaste not found. Ensure you are on macOS with necessary tools.")
            return None
    elif platform.system() == "Linux":
        # Check if running under Wayland
        wayland = os.environ.get('XDG_SESSION_TYPE') == 'wayland'
        if wayland:
            # Check if wl-clipboard tools are available
            try:
                subprocess.run(["wl-paste"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                return "wl-clipboard"
            except FileNotFoundError:
                print("Detected Wayland session. Consider installing wl-clipboard: `sudo apt install wl-clipboard`.")
                return None
        else:
            for tool in ['xclip', 'xsel']:
                try:
                    subprocess.run([tool, "-selection", "clipboard", "-o"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    return tool
                except FileNotFoundError:
                    print(f"{tool} not found. Try installing it using your package manager.")
            print("No supported clipboard tools found. Please install xclip or xsel.")
            return None
        return None

#Read clipboard content
def clipboard_read(tool):
    if tool == "powershell":
        return subprocess.check_output("powershell Get-Clipboard", shell=True, text=True).strip()
    elif tool == "pbpaste":
        return subprocess.check_output("pbpaste", text=True).strip()
    elif tool == "xclip":
        return subprocess.check_output("xclip -selection clipboard -o", shell=True, text=True).strip()
    elif tool == "wl-clipboard":
        return subprocess.check_output("wl-paste", text=True).strip()

# Write content to clipboard
def clipboard_write(content, tool):
    if tool == "powershell":
        subprocess.run("echo | set /p nul= | powershell Set-Clipboard", shell=True, input=content)
    elif tool == "pbcopy":
        subprocess.run("pbcopy", text=True, input=content)
    elif tool == "xclip":
        subprocess.run(f"echo '{content}' | xclip -selection clipboard -i", shell=True)
    elif tool == "wl-clipboard":
        # Escape the content to handle special characters properly
        escaped_content = content.replace("'", "'\"'\"'")
        subprocess.run(f"echo '{escaped_content}' | wl-copy", shell=True)

# Sanitize clipboard contents
def sanitize_clipboard(content, rules):
    for pattern in rules:
        # Escape the hyphen in character ranges or consider explicitly defining ranges
        safe_pattern = re.sub(r'(?<!\\)-', r'\-', pattern['pattern'])  # Escape unescaped hyphens
        regex = re.compile(safe_pattern)
        content = regex.sub(pattern['replacement'], content)
    return content

def get_desktop_environment():
    # Check XDG_CURRENT_DESKTOP first
    desktop_env = os.environ.get('XDG_CURRENT_DESKTOP', '')

    # If it contains 'ubuntu', check for GNOME processes
    if 'ubuntu' in desktop_env.lower():
        try:
            # Check for gnome-shell process as an indication of GNOME
            processes = subprocess.check_output(['pgrep', 'gnome-shell'], text=True)
            if processes:
                return 'GNOME'
        except subprocess.CalledProcessError:
            return None  # gnome-shell is not running

    # Fallback to basic string comparisons
    if 'gnome' in desktop_env.lower():
        return 'GNOME'
    elif 'xfce' in desktop_env.lower():
        return 'XFCE'

    return None  # Return None if the desktop environment cannot be determined

def is_hotkey_configured():
    if platform.system() == "Linux":
        desktop_env = get_desktop_environment()
        custom_keybinding_command = FULL_COMMAND
        custom_keybinding_name = os.path.splitext(os.path.basename(__file__))[0]

        if desktop_env == "GNOME":
            KEY_SCHEMA = "org.gnome.settings-daemon.plugins.media-keys"
            try:
                # Check if the media-keys schema exists
                schema_check = subprocess.run(
                    f"gsettings list-schemas | {KEY_SCHEMA}",
                    shell=True, capture_output=True)
                
                if schema_check.returncode != 0:
                    return False

                # Get existing hotkeys
                gnome_hotkey = subprocess.check_output(
                    ["gsettings", "get", f"{KEY_SCHEMA}", "custom-keybindings"],
                    text=True
                )
                
                try:
                    keybindings = eval(gnome_hotkey.strip())

                    
                    # Check if the keybinding command is properly set
                    for keybinding in keybindings:
                        name_check = subprocess.check_output(
                            ["gsettings", "get", f"{KEY_SCHEMA}.custom-keybinding:{keybinding}", "name"],
                            text=True
                        )
                        if name_check.strip("<>").split("'")[1] == custom_keybinding_name:  # Adjust to your command
                            return True
                except Exception as e:
                    return False
            except subprocess.CalledProcessError:
                print("Could not query GNOME hotkey configuration. Ensure gsettings is available.")
        elif desktop_env == "XFCE":
            try:
                xfce_hotkey = subprocess.check_output(["xfconf-query", "-c", "keyboard-shortcuts", "-p", f"/CustomShortcut/{custom_keybinding_name}"], text=True)
                if xfce_hotkey:
                    return True
            except subprocess.CalledProcessError:
                print("Could not query XFCE hotkey configuration. Ensure xfconf-query is available.")

    elif platform.system() == "Windows":
        return False  # Assume no hotkey configured unless explicitly known.

    elif platform.system() == "Darwin":
        return False  # Assume no hotkey configured unless explicitly known.

    return False  # Defaults to no hotkey configured.


def setup_hotkey():
    if platform.system() == "Linux":
        desktop_env = get_desktop_environment()
        custom_keybinding_command = FULL_COMMAND
        custom_keybinding_name = os.path.splitext(os.path.basename(__file__))[0]
        if desktop_env == "GNOME":
            KEY_SCHEMA = "org.gnome.settings-daemon.plugins.media-keys"
            # Check schema availability
            schema_check = subprocess.run(
                f"gsettings list-schemas | grep {KEY_SCHEMA}",
                shell=True, capture_output=True
            )

            if schema_check.returncode != 0:
                print("Required schema not found. Please ensure you are using GNOME.")
                return

            # Clear existing custom keybindings
            #subprocess.run("gsettings set org.gnome.settings-daemon.plugins.media-keys custom-keybindings '[]'", shell=True)

            # Prepare path for the new custom keybinding
            new_keybinding_path = f'/org/gnome/settings-daemon/plugins/media-keys/custom-keybinding/{custom_keybinding_name}/'

            # Set up the new custom keybinding
            subprocess.run(f"gsettings set {KEY_SCHEMA}.custom-keybinding:{new_keybinding_path} name {custom_keybinding_name}", shell=True, check=True)
            subprocess.run(f"gsettings set {KEY_SCHEMA}.custom-keybinding:{new_keybinding_path} command '{custom_keybinding_command}'", shell=True, check=True)
            subprocess.run(f"gsettings set {KEY_SCHEMA}.custom-keybinding:{new_keybinding_path} binding '{HOTKEY}'", shell=True, check=True)

            # Register the new keybinding
            subprocess.run(f"gsettings set org.gnome.settings-daemon.plugins.media-keys custom-keybindings \"['{new_keybinding_path}']\"", shell=True, check=True)

            print(f"Hotkey '{HOTKEY}' set successfully for GNOME.")

        elif desktop_env == "XFCE":
            try:
                xfce_command = f"xfconf-query -c keyboard-shortcuts -p '/CustomShortcut/custom0' -n -s '{custom_keybinding_command}'"
                subprocess.run(xfce_command, shell=True, check=True)
                print("Hotkey set successfully for XFCE.")
            except Exception as e:
                print("Failed to set hotkey for XFCE:", e)

    elif platform.system() == "Windows":
        try:
            import win32api
            import win32con

            # Register the hotkey
            win32api.RegisterHotKey(None, 1, win32con.MOD_CONTROL | win32con.MOD_ALT, ord('C'))
            print("Hotkey set successfully for Windows.")
        except Exception as e:
            print("Failed to set hotkey for Windows:", e)

    elif platform.system() == "Darwin":
        try:
            # macOS does not have a native way to set hotkeys like Linux does.
            print("Manual setup is required for macOS hotkeys. Consider using a tool like Automator or Keyboard Maestro.")
        except Exception as e:
            print("Failed to provide guidance for macOS hotkey setup:", e)

    else:
        print(f"Hotkey setup not supported for {platform.system()}.")

# Remove hotkey for GNOME or XFCE
def remove_hotkey():
    if platform.system() == "Linux":
        desktop_env = get_desktop_environment()
        custom_keybinding_command = FULL_COMMAND
        custom_keybinding_name = os.path.splitext(os.path.basename(__file__))[0]
        if desktop_env == "GNOME":
            KEY_SCHEMA = "org.gnome.settings-daemon.plugins.media-keys"
            try:
                # Verify required schema exists
                schema_check = subprocess.run(
                    f"gsettings list-schemas | grep {KEY_SCHEMA}",
                    shell=True, capture_output=True
                )
                
                if schema_check.returncode != 0:
                    print("Required schema not found. Cannot remove hotkey.")
                    return

                # Get existing custom keybindings
                keybindings_output = subprocess.run(
                    f"gsettings get {KEY_SCHEMA} custom-keybindings",
                    shell=True, capture_output=True, text=True
                )

                # Get existing hotkeys
                gnome_hotkey = subprocess.check_output(
                    ["gsettings", "get", f"{KEY_SCHEMA}", "custom-keybindings"],
                    text=True
                )
                
                try:
                    keybindings = eval(gnome_hotkey.strip())

                    # Check if the keybinding command is properly set
                    for keybinding in keybindings:
                        name_check = subprocess.check_output(
                            ["gsettings", "get", f"{KEY_SCHEMA}.custom-keybinding:{keybinding}", "name"],
                            text=True
                        )
                        if name_check.strip("<>").split("'")[1] == custom_keybinding_name:  # Adjust to your command
                            keybinding_path = f'/org/gnome/settings-daemon/plugins/media-keys/custom-keybinding/{custom_keybinding_name}/'
                            # Set up the new custom keybinding
                            subprocess.run(f"gsettings reset {KEY_SCHEMA}.custom-keybinding:{keybinding_path} name", shell=True, check=True)
                            subprocess.run(f"gsettings reset {KEY_SCHEMA}.custom-keybinding:{keybinding_path} command", shell=True, check=True)
                            subprocess.run(f"gsettings reset {KEY_SCHEMA}.custom-keybinding:{keybinding_path} binding", shell=True, check=True)
                            print(f"Hotkey '{HOTKEY}' removed successfully for GNOME.")
                            return True
                except Exception as e:
                    return False
            except subprocess.CalledProcessError as e:
                print(f"Failed to query or remove hotkey for GNOME. Error: {e}")
        elif desktop_env == "XFCE":
            try:
                xfce_command = "xfconf-query -c keyboard-shortcuts -p '/CustomShortcut/custom0' -r"
                subprocess.run(xfce_command, shell=True, check=True)
                print(f"Hotkey '{HOTKEY}' removed successfully for XFCE.")
            except Exception as e:
                print("Failed to remove hotkey for XFCE:", e)
    else:
        print(f"Hotkey removal not supported for {platform.system()}.")

# simulate paste implementations
def simulate_paste_wayland():
    return False

def simulate_paste_x11():
    if not shutil.which("xdotool"):
        return False
    try:
        subprocess.run(["xdotool", "key", "--clearmodifiers", "ctrl+v"], check=True)
        return True
    except Exception:
        return False

def simulate_paste_macos():
    # Use AppleScript to send Cmd+V to the frontmost app
    # Note: requires accessibility permission for osascript to control GUI in some macOS versions.
    applescript = 'tell application "System Events" to keystroke "v" using command down'
    try:
        subprocess.run(["osascript", "-e", applescript], check=True)
        return True
    except Exception:
        return False

def simulate_paste_windows():
    # Use SendInput to send Ctrl+V
    # Based on WinAPI INPUT/KEYBDINPUT structures
    try:
        user32 = ctypes.windll.user32
        VK_CONTROL = 0x11
        V_KEY_V = 0x56

        # key event constants
        KEYEVENTF_KEYUP = 0x0002

        # press Ctrl
        user32.keybd_event(VK_CONTROL, 0, 0, 0)
        # press V
        user32.keybd_event(V_KEY_V, 0, 0, 0)
        # release V
        user32.keybd_event(V_KEY_V, 0, KEYEVENTF_KEYUP, 0)
        # release Ctrl
        user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
        return True
    except Exception:
        return False

# Main function to automate the clipboard sanitization and paste
def main():
    parser = argparse.ArgumentParser(description="Clipboard-privacy")
    parser.add_argument('--setup', action='store_true', help='Set up a hotkey for clipboard sanitization.')
    parser.add_argument('--remove', action='store_true', help='Remove the configured hotkey for clipboard sanitization.')
    args = parser.parse_args()

    settings = load_settings(os.path.join(SCRIPT_PATH,SETTINGS_FILE))
    if args.setup:
        setup_hotkey()
    elif args.remove:
        remove_hotkey()
    else:
        if not is_hotkey_configured():
            print("No hotkey is currently set. You can add one using the --setup option.")

        tool = check_clipboard_tools()
        if not tool:
            return  # Missing tools prompt already displayed
        try:
            clip_content = clipboard_read(tool)
            rules = settings.get('rules', [])
            sanitized_content = sanitize_clipboard(clip_content, rules)
            clipboard_write(sanitized_content, tool) 
            if platform.system() == "Windows":
                if simulate_paste_windows()
                    clipboard_write(clip_content, tool) 
            elif platform.system() == "Darwin":
                if simulate_paste_macos()
                    clipboard_write(clip_content, tool) 
            elif platform.system() == "Linux":
                # Check if running under Wayland
                wayland = os.environ.get('XDG_SESSION_TYPE') == 'wayland'
                if wayland:
                    if simulate_paste_wayland()
                        clipboard_write(clip_content, tool) 
                else:
                    if simulate_paste_x11()
                        clipboard_write(clip_content, tool) 

        except Exception as e:
            print(f"Error: {e}")

# Check for compatible Python version
def check_python_version():
    if sys.version_info < (3, 6):  # Check if Python version is less than 3.6
        print("Error: Python 3.6 or higher is required.")
        sys.exit(1)

if __name__ == "__main__":
    check_python_version()
    main()