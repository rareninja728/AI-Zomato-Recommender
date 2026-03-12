import os
import subprocess
import sys
from pathlib import Path

def start_server():
    """Lauches the Zomato AI backend server on port 8000."""
    print("=" * 60)
    print("  Zomato AI Recommendation Service - Backend Launcher")
    print("=" * 60)
    
    # Path to the Phase 5 directory
    phase5_dir = Path(__file__).parent / "PHASE 5"
    
    # Use the current python executable to run uvicorn
    # This ensures that we use the same environment that this script is running in
    cmd = [
        sys.executable, "-m", "uvicorn", "src.main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
    ]
    
    print(f"\n[INFO] Starting backend in: {phase5_dir}")
    print(f"[INFO] Command: {' '.join(cmd)}")
    print("-" * 60)
    
    try:
        # Change current working directory to the Phase 5 folder
        os.chdir(phase5_dir)
        
        # Open the browser in a separate thread/process so it doesn't block
        import webbrowser
        import threading
        import time

        def open_browser():
            time.sleep(3) # Wait for server to be ready
            webbrowser.open("http://localhost:8000")
            print("[INFO] Opened Zomato AI in your default browser.")

        threading.Thread(target=open_browser, daemon=True).start()

        # Start the process
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n[INFO] Backend server stopped.")
    except Exception as e:
        print(f"\n[ERROR] Failed to start server: {e}")

if __name__ == "__main__":
    start_server()
