import basic
import os
import platform

def clear_screen():
    # Clear screen command based on the operating system
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')

clear_screen()

def find_module_path(module_name):
  # Check built-in modules first
  builtin_path = os.path.join(os.path.dirname(__file__), 'modules', f"{module_name}.txt")
  if os.path.exists(builtin_path):
    return builtin_path
      
  # Check stdlib directory
  stdlib_path = os.path.join('stdlib', f"{module_name}.txt")
  if os.path.exists(stdlib_path):
    return stdlib_path
      
  # Check current directory
  local_path = f"{module_name}.txt"
  if os.path.exists(local_path):
    return local_path
      
  return None


while True:
    text = input('$ ')
    
    if text.strip().lower() == "exit":
      break
  
    elif text.strip().lower() == "scatter":
      clear_screen()
      continue  # Skip the rest of the loop and show fresh prompt

    elif text.strip() == "":
      continue

    elif text.startswith("build "):
      filename = text[6:].strip()
      try:
        with open(filename, 'r') as f:
          code = f.read()
        result, error = basic.validate(code)
        if error:
          print(f"Build failed:\n{error.as_string()}")
        else:
          print(f"✅ {result} - No syntax errors")
      except FileNotFoundError:
        print(f"Error: File '{filename}' not found")
      continue

    elif text == "build --help":
      print("JhayScript Build System")
      print("Usage:")
      print("  build <filename>    - Validate syntax")
      print("  build --version     - Show compiler version")
      print("  build --verbose     - Show detailed output")

    elif text == "build --version":
      print(f"JhayScript Compiler v1.0")

    elif text.startswith("build --verbose "):
      filename = text[16:].strip()
      try:
        with open(filename, 'r') as f:
          code = f.read()
        
        # Show tokens
        print("\n=== TOKENS ===")
        tokens, error = basic.get_tokens(code)
        if error:
          print(f"Tokenization error:\n{error.as_string()}")
        else:
          for token in tokens:
            print(f"{token['type']}: {repr(token['value']) if token['value'] is not None else ''} (at {token['position']})")
        
        # Show AST
        print("\n=== ABSTRACT SYNTAX TREE ===")
        ast, error = basic.get_ast(code)
        if error:
          print(f"Parsing error:\n{error.as_string()}")
        else:
          # Pretty print the AST
          import pprint
          pp = pprint.PrettyPrinter(indent=2)
          pp.pprint(ast)
        
        # Final validation
        result, error = basic.validate(code)
        if error:
          print(f"\nBuild failed:\n{error.as_string()}")
        else:
          print(f"\n✅ {result} - No syntax errors")
              
      except FileNotFoundError:
        print(f"Error: File '{filename}' not found")
      continue
  
    result, error = basic.run('<stdin>', text)

    if error:
      print(error.as_string())
    elif result:
      if len(result.elements) == 1:
        print(repr(result.elements[0]))
    else:
      print(repr(result))
