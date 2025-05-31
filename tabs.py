def spaces_to_tabs(filename, spaces_per_tab=4):
    with open(filename, 'r') as file:
        lines = file.readlines()

    with open(filename, 'w') as file:
        for line in lines:
            leading_spaces = len(line) - len(line.lstrip(' '))
            tabs = '\t' * (leading_spaces // spaces_per_tab)
            new_line = tabs + line.lstrip(' ')
            file.write(new_line)

# Replace with your actual filename
spaces_to_tabs("basic.py")
