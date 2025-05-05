import subprocess
import sys
import time

def run_script(script_name):
    """
    Run a Python script and handle any errors that occur.
    """
    try:
        print(f"\nRunning {script_name}...")
        result = subprocess.run([sys.executable, script_name], check=True)
        print(f"{script_name} completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running {script_name}. Error code: {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"Error: {script_name} not found in current directory")
        return False


def main():
    # List of scripts to run
    scripts = ['youtube_api.py', 'chatgpt_api.py']
    
    # Run each script sequentially
    for script in scripts:
        success = run_script(script)
        if not success:
            print(f"Stopping execution due to error in {script}")
            sys.exit(1)
        time.sleep(1)  # Small delay between scripts
        
    print("\nAll scripts completed successfully!")


if __name__ == "__main__":
    main()