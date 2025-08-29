#!/usr/bin/env python3
"""Simple launcher for visualization tools."""

import sys
import subprocess
from pathlib import Path

def main():
    """Launch the enhanced visualization tools."""
    current_dir = Path(__file__).parent
    launcher_path = current_dir / "visualization" / "visualize_launcher.py"
    
    if launcher_path.exists():
        # Pass all arguments to the enhanced launcher
        args = [sys.executable, str(launcher_path)] + sys.argv[1:]
        result = subprocess.run(args)
        sys.exit(result.returncode)
    else:
        print("❌ Enhanced visualization tools not found!")
        print("Please run from the project root directory.")
        sys.exit(1)

if __name__ == "__main__":
    main()
