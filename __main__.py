import sys
import os
from basic import run

# Add these constants at the top of your file
VERSION = "1.0"  # Update this with your actual version
HELP_TEXT = """JhayScript v{version}
Usage: jhayscript [options] <filename>

Options:
  --version      Show version information
  --help         Show this help message
  --examples     Show example scripts
"""

def show_version():
    print(f"JhayScript v{VERSION}")

def show_help():
    print(HELP_TEXT.format(version=VERSION))

def show_examples():
    print("""Example scripts:
  1. hello.jhay:
    echo "Hello, World!"
    
  2. calculator.jhay:
    a = 10
    b = 5
    echo "Sum: {a + b}"
    """)

def run_script(filename):
    try:
        with open(filename, 'r') as f:
            script = f.read()
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found")
        return
    
    result, error = run(filename, script)
    
    if error:
        print(error.as_string())
    elif result:
        if isinstance(result, (list, tuple)):
            print('\n'.join(map(str, result)))
        else:
            print(result)

def main():
    if len(sys.argv) < 2:
        show_help()
        return
    
    # Handle command-line options
    first_arg = sys.argv[1]
    if first_arg.startswith('--'):
        {
            '--version': show_version,
            '--help': show_help,
            '--examples': show_examples
        }.get(first_arg, show_help)()
        return
    
    # If not a flag, treat as filename
    filename = sys.argv[1]
    run_script(filename)

if __name__ == "__main__":
    main()