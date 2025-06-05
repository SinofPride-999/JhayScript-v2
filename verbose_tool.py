from jhayscript import (
  Lexer,
  Parser,
  NumberNode,
  StringNode,
  VarAccessNode,
  BinOpNode
)

def get_tokens(text):
  """Get tokens with verbose information"""
  lexer = Lexer('<stdin>', text)
  tokens, error = lexer.make_tokens()
  if error: return None, error
  
  token_info = []
  for token in tokens:
    token_info.append({
      'type': token.type,
      'value': token.value,
      'position': f"line {token.pos_start.ln + 1}, col {token.pos_start.col + 1}"
    })
  return token_info, None

def get_ast(text):
  """Get AST with verbose information"""
  lexer = Lexer('<stdin>', text)
  tokens, error = lexer.make_tokens()
  if error: return None, error
  
  parser = Parser(tokens)
  ast = parser.parse()
  if ast.error: return None, ast.error
  
  # Simple AST representation
  def node_to_dict(node):
    if isinstance(node, NumberNode):
      return {'type': 'NumberNode', 'value': node.tok.value}
    elif isinstance(node, StringNode):
      return {'type': 'StringNode', 'value': node.tok.value}
    elif isinstance(node, VarAccessNode):
      return {'type': 'VarAccessNode', 'name': node.var_name_tok.value}
    elif isinstance(node, BinOpNode):
      return {
        'type': 'BinOpNode',
        'left': node_to_dict(node.left_node),
        'op': node.op_tok.type,
        'right': node_to_dict(node.right_node)
      }
    # Add more node types as needed
    else:
      return str(node)  # Fallback for unhandled node types
  
  return node_to_dict(ast.node), None