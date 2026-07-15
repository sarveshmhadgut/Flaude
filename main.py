import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    app_path = Path(__file__).parent / "src" / "ui" / "app.py"

    if not app_path.exists():
        print(f"Error: Could not find the Streamlit app-'{app_path}'")
        sys.exit(1)

    command = [sys.executable, "-m", "streamlit", "run", str(app_path)] + sys.argv[1:]

    try:
        subprocess.run(command, check=True)
    except KeyboardInterrupt:
        sys.exit(0)
