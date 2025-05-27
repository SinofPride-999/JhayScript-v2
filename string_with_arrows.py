def string_with_arrows(text, pos_start, pos_end):
    result = ''
    tok_op = -1

    # Calculate indices
    idx_start = text.rfind('\n', 0, pos_start.idx)
    if idx_start == -1: idx_start = 0
    else: idx_start += 1

    idx_end = text.find('\n', idx_start)
    if idx_end == -1: idx_end = len(text)

    # Generate each line
    line = text[idx_start:idx_end]
    col_start = pos_start.col
    col_end = pos_end.col

    # Append to result
    result += line + '\n'
    result += ' ' * col_start + '^' * max(1, col_end - col_start)

    return result.replace('\t', '')
