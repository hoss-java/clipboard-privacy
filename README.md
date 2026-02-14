## Clipboard Privacy

Short description
A cross-platform Python script that reads the clipboard, removes sensitive data based on JSON rules, writes the sanitized text back to the clipboard, and optionally attempts to simulate a paste into the foreground application. Supports Linux (Wayland/X11), Windows, macOS.

Requirements
- Python 3.6+
- wl-clipboard (wl-copy / wl-paste) on Wayland Linux
- xclip or xsel for X11 Linux (one required)
- On macOS: pbcopy / pbpaste (usually available)
- On Windows: PowerShell accessible (Get-Clipboard / Set-Clipboard)
- PyPI (optional, for DBus/portal usage): pydbus, gi (for advanced Wayland portal features)

Files
- clipboard-privacy.json — JSON rules file (pattern/replacement list)
- script file (the provided Python script)

Quick start
1. Place the script and clipboard-privacy.json in the same directory.
2. Edit clipboard-privacy.json to add your sanitization rules. Format:
   [
     { "pattern": "\\bSECRET_TOKEN\\b", "replacement": "[REDACTED]" },
     { "pattern": "user@example\\.com", "replacement": "[EMAIL]" }
   ]
3. Run:
   python3 clipboard_privacy.py
   - By default it reads the clipboard, sanitizes, and writes the sanitized text back.
4. Optional flags:
   --setup     Set up the configured hotkey (Linux desktop-specific).
   --remove    Remove the configured hotkey.

Behavior details
- Rules: loaded from clipboard-privacy.json; must be a list under the top-level "rules" key or be a raw list. Each rule is an object with:
  - pattern: a regular expression (Python re). Patterns are applied with re.sub().
  - replacement: replacement text.
- System-aware rules: the script augments rules with system-specific patterns (current username and hostname on Linux).
- Clipboard backends:
  - Wayland: wl-copy / wl-paste
  - X11: xclip or xsel
  - macOS: pbcopy / pbpaste
  - Windows: PowerShell Get-Clipboard / Set-Clipboard
- Paste simulation:
  - X11: can attempt to send key events (xdotool or XSendEvent), if available.
  - Wayland: requires xdg-desktop-portal input/remote desktop support and user permission. Not universally available.
  - macOS: can use osascript/AppleScript (requires Accessibility permission).
  - Windows: can use WinAPI SendInput.
  - Note: paste simulation is platform- and compositor-dependent; the script defaults to writing sanitized content to the clipboard and will only attempt simulated paste if supported and enabled in code.

Configuration examples
- Simple JSON with two rules:
  {
    "rules": [
      { "pattern": "\\b\\d{16}\\b", "replacement": "[CARD]" },
      { "pattern": "\\b\\d{3}-\\d{2}-\\d{4}\\b", "replacement": "[SSN]" }
    ]
  }

Security & privacy
- All processing is local to your machine; the script reads and writes the clipboard only on the host.
- Be careful when configuring paste simulation: portals or system APIs may prompt for permission.

Troubleshooting
- "Tool not found" messages: install the appropriate clipboard utility for your platform (wl-clipboard, xclip, xsel, pbcopy, PowerShell).
- Wayland paste simulation fails: ensure xdg-desktop-portal is running and your compositor supports Input/RemoteDesktop.
- Hotkey setup: desktop-specific commands are required (GNOME/XFCE). The script contains placeholders to implement those commands for your environment.

Extending the script
- Add or refine JSON rules (regular expressions) to match your sensitive data patterns.
- Implement desktop-specific hotkey registration commands for GNOME (gsettings) and XFCE (xfconf-query).
- Implement portal-based input simulation with pydbus (xdg-desktop-portal) for Wayland; or use platform-specific APIs for macOS/Windows.
- Improve MIME handling if you need to support non-text clipboard data.

License
Add your preferred license text here.

Contact / Contribution
Open issues or submit pull requests on your repository.