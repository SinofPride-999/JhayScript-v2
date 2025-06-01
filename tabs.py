import sys

def convert_spaces_to_tabs(filename, spaces_per_tab=4):
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    new_lines = []
    for line in lines:
        leading_spaces = len(line) - len(line.lstrip(' '))
        if leading_spaces > 0:
            tabs = leading_spaces // spaces_per_tab
            remaining_spaces = leading_spaces % spaces_per_tab
            new_line = ('\t' * tabs) + (' ' * remaining_spaces) + line.lstrip(' ')
        else:
            new_line = line
        new_lines.append(new_line)
    
    with open(filename, 'w') as f:
        f.writelines(new_lines)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python spaces_to_tabs.py <filename> [spaces_per_tab]")
        sys.exit(1)
    
    filename = sys.argv[1]
    spaces_per_tab = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    convert_spaces_to_tabs(filename, spaces_per_tab)
    print(f"Converted {filename} from spaces to tabs.")