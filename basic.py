#######################################
# IMPORTS
#######################################

from strings_with_arrows import *

import string
import os
import math
import random
import time
import threading
import queue

#######################################
# CONSTANTS
#######################################

DIGITS = '0123456789'
LETTERS = string.ascii_letters
LETTERS_DIGITS = LETTERS + DIGITS

#######################################
# ERRORS
#######################################

class Error:
  def __init__(self, pos_start, pos_end, error_name, details):
    self.pos_start = pos_start
    self.pos_end = pos_end
    self.error_name = error_name
    self.details = details

  def as_string(self):
    result  = f'{self.error_name}: {self.details}\n'
    result += f'File {self.pos_start.fn}, line {self.pos_start.ln + 1}'
    result += '\n\n' + string_with_arrows(self.pos_start.ftxt, self.pos_start, self.pos_end)
    return result

class IllegalCharError(Error):
  def __init__(self, pos_start, pos_end, details):
    super().__init__(pos_start, pos_end, 'Illegal Character', details)

class ExpectedCharError(Error):
  def __init__(self, pos_start, pos_end, details):
    super().__init__(pos_start, pos_end, 'Expected Character', details)

class InvalidSyntaxError(Error):
  def __init__(self, pos_start, pos_end, details=''):
    super().__init__(pos_start, pos_end, 'Invalid Syntax', details)

class RTError(Error):
  def __init__(self, pos_start, pos_end, details, context):
    super().__init__(pos_start, pos_end, 'Runtime Error', details)
    self.context = context

  def as_string(self):
    result  = self.generate_traceback()
    result += f'{self.error_name}: {self.details}'
    result += '\n\n' + string_with_arrows(self.pos_start.ftxt, self.pos_start, self.pos_end)
    return result

  def generate_traceback(self):
    result = ''
    pos = self.pos_start
    ctx = self.context

    while ctx:
      result = f'  File {pos.fn}, line {str(pos.ln + 1)}, in {ctx.display_name}\n' + result
      pos = ctx.parent_entry_pos
      ctx = ctx.parent

    return 'Traceback (most recent call last):\n' + result

#######################################
# POSITION
#######################################

class Position:
  def __init__(self, idx, ln, col, fn, ftxt):
    self.idx = idx
    self.ln = ln
    self.col = col
    self.fn = fn
    self.ftxt = ftxt

  def advance(self, current_char=None):
    self.idx += 1
    self.col += 1

    if current_char == '\n':
      self.ln += 1
      self.col = 0

    return self

  def copy(self):
    return Position(self.idx, self.ln, self.col, self.fn, self.ftxt)

#######################################
# TOKENS
#######################################

TT_INT				= 'INT'
TT_FLOAT    	= 'FLOAT'
TT_STRING			= 'STRING'
TT_IDENTIFIER	= 'IDENTIFIER'
TT_KEYWORD		= 'KEYWORD'
TT_PLUS     	= 'PLUS'
TT_MINUS    	= 'MINUS'
TT_MUL      	= 'MUL'
TT_DIV      	= 'DIV'
TT_POW				= 'POW'
TT_EQ					= 'EQ'
TT_LPAREN   	= 'LPAREN'
TT_RPAREN   	= 'RPAREN'
TT_LSQUARE    = 'LSQUARE'
TT_RSQUARE    = 'RSQUARE'
TT_LBRACE     = 'LBRACE'
TT_RBRACE     = 'RBRACE'
TT_EE					= 'EE'
TT_NE					= 'NE'
TT_LT					= 'LT'
TT_GT					= 'GT'
TT_LTE				= 'LTE'
TT_GTE				= 'GTE'
TT_COMMA			= 'COMMA'
TT_ARROW			= 'ARROW'
TT_NEWLINE		= 'NEWLINE'
TT_EOF				= 'EOF'
TT_IMPORT     = 'IMPORT'
TT_FROM       = 'FROM'
TT_AS         = 'AS'
TT_MOD        = 'MOD'
TT_ASYNC      = 'ASYNC'
TT_AWAIT      = 'AWAIT'

KEYWORDS = [
  'initiate',
  
  'and',
  'or',
  'not',
  
  'if',
  'elif',
  'else',
  'for',
  'to',
  'step',
  'while',
  'function',
  'THEN',
  'END',
  
  'return',
  'continue',
  'break',
  
  'fuck_around',
  'find_out',
  
  'import',
  'from',
  'as',
  
  'async',
  'await',
  'sleep'
]

class Token:
  def __init__(self, type_, value=None, pos_start=None, pos_end=None):
    self.type = type_
    self.value = value

    if pos_start:
      self.pos_start = pos_start.copy()
      self.pos_end = pos_start.copy()
      self.pos_end.advance()

    if pos_end:
      self.pos_end = pos_end.copy()

  def matches(self, type_, value):
    return self.type == type_ and self.value == value

  def __repr__(self):
    if self.value: return f'{self.type}:{self.value}'
    return f'{self.type}'

#######################################
# LEXER
#######################################

class Lexer:
  def __init__(self, fn, text):
    self.fn = fn
    self.text = text
    self.pos = Position(-1, 0, -1, fn, text)
    self.current_char = None
    self.advance()

  def advance(self):
    self.pos.advance(self.current_char)
    self.current_char = self.text[self.pos.idx] if self.pos.idx < len(self.text) else None

  def make_tokens(self):
    tokens = []

    while self.current_char != None:
      if self.current_char in ' \t':
        self.advance()
        
      elif self.current_char == ':':
        # Check if this is the start of a comment
        next_char = self.text[self.pos.idx + 1] if self.pos.idx + 1 < len(self.text) else None
        if next_char == ':':
          self.skip_comment()
        else:
          pos_start = self.pos.copy()
          char = self.current_char
          self.advance()
          return [], IllegalCharError(pos_start, self.pos, "'" + char + "'")
        
      elif self.current_char in ';\n':
        tokens.append(Token(TT_NEWLINE, pos_start=self.pos))
        self.advance()
        
      elif self.current_char in DIGITS:
        tokens.append(self.make_number())
        
      elif self.current_char in LETTERS:
        tokens.append(self.make_identifier())
        
      elif self.current_char in ('"', "'"):  # Handle both single and double quotes
        token, error = self.make_string()
        if error: return [], error
        tokens.append(token)
        
      elif self.current_char == '{':
        tokens.append(Token(TT_LBRACE, pos_start=self.pos))
        self.advance()
        
      elif self.current_char == '}':
        tokens.append(Token(TT_RBRACE, pos_start=self.pos))
        self.advance()
        
      elif self.current_char == '"':
        tokens.append(self.make_string())
        
      elif self.current_char == '+':
        tokens.append(Token(TT_PLUS, pos_start=self.pos))
        self.advance()
        
      elif self.current_char == '-':
        tokens.append(self.make_minus_or_arrow())
        
      elif self.current_char == '*':
        tokens.append(Token(TT_MUL, pos_start=self.pos))
        self.advance()
        
      elif self.current_char == '%':
        tokens.append(Token(TT_MOD, pos_start=self.pos))
        self.advance()
        
      elif self.current_char == '/':
        tokens.append(Token(TT_DIV, pos_start=self.pos))
        self.advance()
        
      elif self.current_char == '^':
        tokens.append(Token(TT_POW, pos_start=self.pos))
        self.advance()
        
      elif self.current_char == '(':
        tokens.append(Token(TT_LPAREN, pos_start=self.pos))
        self.advance()
        
      elif self.current_char == ')':
        tokens.append(Token(TT_RPAREN, pos_start=self.pos))
        self.advance()
        
      elif self.current_char == '[':
        tokens.append(Token(TT_LSQUARE, pos_start=self.pos))
        self.advance()
        
      elif self.current_char == ']':
        tokens.append(Token(TT_RSQUARE, pos_start=self.pos))
        self.advance()
        
      elif self.current_char == '!':
        token, error = self.make_not_equals()
        if error: return [], error
        tokens.append(token)
        
      elif self.current_char == '=':
        tokens.append(self.make_equals())
        
      elif self.current_char == '<':
        tokens.append(self.make_less_than())
        
      elif self.current_char == '>':
        tokens.append(self.make_greater_than())
        
      elif self.current_char == ',':
        tokens.append(Token(TT_COMMA, pos_start=self.pos))
        self.advance()
        
      else:
        pos_start = self.pos.copy()
        char = self.current_char
        self.advance()
        return [], IllegalCharError(pos_start, self.pos, "'" + char + "'")

    tokens.append(Token(TT_EOF, pos_start=self.pos))
    return tokens, None

  def make_number(self):
    num_str = ''
    dot_count = 0
    pos_start = self.pos.copy()

    while self.current_char != None and self.current_char in DIGITS + '.':
      if self.current_char == '.':
        if dot_count == 1: break
        dot_count += 1
      num_str += self.current_char
      self.advance()

    if dot_count == 0:
      return Token(TT_INT, int(num_str), pos_start, self.pos)
    else:
      return Token(TT_FLOAT, float(num_str), pos_start, self.pos)

  def make_string(self):
    string = ''
    pos_start = self.pos.copy()
    escape_character = False
    quote_char = self.current_char
    self.advance()

    escape_characters = {
      'n': '\n',
      't': '\t'
    }

    while self.current_char != None and (self.current_char != quote_char or escape_character):
        if escape_character:
            string += escape_characters.get(self.current_char, self.current_char)
            escape_character = False
        else:
            if self.current_char == '\\':
                escape_character = True
            else:
                string += self.current_char
        self.advance()

    if self.current_char != quote_char:
        return None, IllegalCharError(pos_start, self.pos, f"Expected closing quote {quote_char}")

    self.advance()
    return Token(TT_STRING, string, pos_start, self.pos), None

  def make_identifier(self):
    id_str = ''
    pos_start = self.pos.copy()

    while self.current_char != None and self.current_char in LETTERS_DIGITS + '_':
      id_str += self.current_char
      self.advance()

    tok_type = TT_KEYWORD if id_str in KEYWORDS else TT_IDENTIFIER
    return Token(tok_type, id_str, pos_start, self.pos)

  def make_minus_or_arrow(self):
    tok_type = TT_MINUS
    pos_start = self.pos.copy()
    self.advance()

    if self.current_char == '>':
      self.advance()
      tok_type = TT_ARROW

    return Token(tok_type, pos_start=pos_start, pos_end=self.pos)

  def make_not_equals(self):
    pos_start = self.pos.copy()
    self.advance()

    if self.current_char == '=':
      self.advance()
      return Token(TT_NE, pos_start=pos_start, pos_end=self.pos), None

    self.advance()
    return None, ExpectedCharError(pos_start, self.pos, "'=' (after '!')")

  def make_equals(self):
    tok_type = TT_EQ
    pos_start = self.pos.copy()
    self.advance()

    if self.current_char == '=':
      self.advance()
      tok_type = TT_EE

    return Token(tok_type, pos_start=pos_start, pos_end=self.pos)

  def make_less_than(self):
    tok_type = TT_LT
    pos_start = self.pos.copy()
    self.advance()

    if self.current_char == '=':
      self.advance()
      tok_type = TT_LTE

    return Token(tok_type, pos_start=pos_start, pos_end=self.pos)

  def make_greater_than(self):
    tok_type = TT_GT
    pos_start = self.pos.copy()
    self.advance()

    if self.current_char == '=':
      self.advance()
      tok_type = TT_GTE

    return Token(tok_type, pos_start=pos_start, pos_end=self.pos)

  def skip_comment(self):
    # Skip both colons
    self.advance()  # first colon
    self.advance()  # second colon

    # Skip everything until newline
    while self.current_char != None and self.current_char != '\n':
        self.advance()

    # Skip the newline character if present
    if self.current_char == '\n':
        self.advance()

#######################################
# NODES
#######################################

class NumberNode:
  def __init__(self, tok):
    self.tok = tok

    self.pos_start = self.tok.pos_start
    self.pos_end = self.tok.pos_end

  def __repr__(self):
    return f'{self.tok}'

class StringNode:
  def __init__(self, tok):
    self.tok = tok

    self.pos_start = self.tok.pos_start
    self.pos_end = self.tok.pos_end

  def __repr__(self):
    return f'{self.tok}'

class ListNode:
  def __init__(self, element_nodes, pos_start, pos_end):
    self.element_nodes = element_nodes

    self.pos_start = pos_start
    self.pos_end = pos_end

class VarAccessNode:
  def __init__(self, var_name_tok):
    self.var_name_tok = var_name_tok

    self.pos_start = self.var_name_tok.pos_start
    self.pos_end = self.var_name_tok.pos_end

class VarAssignNode:
  def __init__(self, var_name_tok, value_node):
    self.var_name_tok = var_name_tok
    self.value_node = value_node

    self.pos_start = self.var_name_tok.pos_start
    self.pos_end = self.value_node.pos_end

class BinOpNode:
  def __init__(self, left_node, op_tok, right_node):
    self.left_node = left_node
    self.op_tok = op_tok
    self.right_node = right_node

    self.pos_start = self.left_node.pos_start
    self.pos_end = self.right_node.pos_end

  def __repr__(self):
    return f'({self.left_node}, {self.op_tok}, {self.right_node})'

class UnaryOpNode:
  def __init__(self, op_tok, node):
    self.op_tok = op_tok
    self.node = node

    self.pos_start = self.op_tok.pos_start
    self.pos_end = node.pos_end

  def __repr__(self):
    return f'({self.op_tok}, {self.node})'

class IfNode:
  def __init__(self, cases, else_case):
    self.cases = cases
    self.else_case = else_case

    self.pos_start = self.cases[0][0].pos_start
    self.pos_end = (self.else_case or self.cases[len(self.cases) - 1])[0].pos_end

class ForNode:
  def __init__(self, var_name_tok, start_value_node, end_value_node, step_value_node, body_node, should_return_null):
    self.var_name_tok = var_name_tok
    self.start_value_node = start_value_node
    self.end_value_node = end_value_node
    self.step_value_node = step_value_node
    self.body_node = body_node
    self.should_return_null = should_return_null

    self.pos_start = self.var_name_tok.pos_start
    self.pos_end = self.body_node.pos_end

class WhileNode:
  def __init__(self, condition_node, body_node, should_return_null):
    self.condition_node = condition_node
    self.body_node = body_node
    self.should_return_null = should_return_null

    self.pos_start = self.condition_node.pos_start
    self.pos_end = self.body_node.pos_end

class TryNode:
  def __init__(self, try_body, catch_var, catch_body, pos_start, pos_end):
    self.try_body = try_body
    self.catch_var = catch_var
    self.catch_body = catch_body
    self.pos_start = pos_start
    self.pos_end = pos_end
    
  def __str__(self):
    return str(self.value)
    
  def __repr__(self):
    return f"<error: {self.value}>"

class FuncDefNode:
  def __init__(self, var_name_tok, arg_name_toks, body_node, should_auto_return):
    self.var_name_tok = var_name_tok
    self.arg_name_toks = arg_name_toks
    self.body_node = body_node
    self.should_auto_return = should_auto_return

    if self.var_name_tok:
      self.pos_start = self.var_name_tok.pos_start
    elif len(self.arg_name_toks) > 0:
      self.pos_start = self.arg_name_toks[0].pos_start
    else:
      self.pos_start = self.body_node.pos_start

    self.pos_end = self.body_node.pos_end

class CallNode:
  def __init__(self, node_to_call, arg_nodes):
    self.node_to_call = node_to_call
    self.arg_nodes = arg_nodes

    self.pos_start = self.node_to_call.pos_start

    if len(self.arg_nodes) > 0:
      self.pos_end = self.arg_nodes[len(self.arg_nodes) - 1].pos_end
    else:
      self.pos_end = self.node_to_call.pos_end

class ReturnNode:
  def __init__(self, node_to_return, pos_start, pos_end):
    self.node_to_return = node_to_return

    self.pos_start = pos_start
    self.pos_end = pos_end

class ContinueNode:
  def __init__(self, pos_start, pos_end):
    self.pos_start = pos_start
    self.pos_end = pos_end

class BreakNode:
  def __init__(self, pos_start, pos_end):
    self.pos_start = pos_start
    self.pos_end = pos_end

class ImportNode:
  def __init__(self, imports, module_path, pos_start, pos_end):
    self.imports = imports  # List of (name, alias) tuples
    self.module_path = module_path
    self.pos_start = pos_start
    self.pos_end = pos_end

  def __repr__(self):
    return f"Import({self.imports} from '{self.module_path}')"

class AsyncNode:
  def __init__(self, node):
    self.node = node
    self.pos_start = node.pos_start
    self.pos_end = node.pos_end

class AwaitNode:
  def __init__(self, node):
    self.node = node
    self.pos_start = node.pos_start
    self.pos_end = node.pos_end

class SleepNode:
  def __init__(self, duration_node, pos_start, pos_end):
    self.duration_node = duration_node
    self.pos_start = pos_start
    self.pos_end = pos_end

#######################################
# PARSE RESULT
#######################################

class ParseResult:
  def __init__(self):
    self.error = None
    self.node = None
    self.last_registered_advance_count = 0
    self.advance_count = 0
    self.to_reverse_count = 0

  def register_advancement(self):
    self.last_registered_advance_count = 1
    self.advance_count += 1

  def register(self, res):
    self.last_registered_advance_count = res.advance_count
    self.advance_count += res.advance_count
    if res.error: self.error = res.error
    return res.node

  def try_register(self, res):
    if res.error:
      self.to_reverse_count = res.advance_count
      return None
    return self.register(res)

  def success(self, node):
    self.node = node
    return self

  def failure(self, error):
    if not self.error or self.last_registered_advance_count == 0:
      self.error = error
    return self

#######################################
# PARSER
#######################################

class Parser:
  def __init__(self, tokens):
    self.tokens = tokens
    self.tok_idx = -1
    self.advance()

  def advance(self):
    self.tok_idx += 1
    self.update_current_tok()
    return self.current_tok

  def reverse(self, amount=1):
    self.tok_idx -= amount
    self.update_current_tok()
    return self.current_tok

  def update_current_tok(self):
    if self.tok_idx >= 0 and self.tok_idx < len(self.tokens):
      self.current_tok = self.tokens[self.tok_idx]

  def parse(self):
    res = self.statements()
    if not res.error and self.current_tok.type != TT_EOF:
      return res.failure(InvalidSyntaxError(
        self.current_tok.pos_start, self.current_tok.pos_end,
        "Token cannot appear after previous tokens"
      ))
    return res

  ###################################

  def statements(self):
    res = ParseResult()
    statements = []
    pos_start = self.current_tok.pos_start.copy()

    while self.current_tok.type == TT_NEWLINE:
      res.register_advancement()
      self.advance()

    statement = res.register(self.statement())
    if res.error: return res
    statements.append(statement)

    more_statements = True

    while True:
      newline_count = 0
      while self.current_tok.type == TT_NEWLINE:
        res.register_advancement()
        self.advance()
        newline_count += 1
      if newline_count == 0:
        more_statements = False

      if not more_statements: break
      statement = res.try_register(self.statement())
      if not statement:
        self.reverse(res.to_reverse_count)
        more_statements = False
        continue
      statements.append(statement)

    return res.success(ListNode(
      statements,
      pos_start,
      self.current_tok.pos_end.copy()
    ))

  def statement(self):
    res = ParseResult()
    pos_start = self.current_tok.pos_start.copy()
    
    if self.current_tok.matches(TT_KEYWORD, 'import'):
      import_res = self.import_statement()
      if import_res.error: return import_res
      return res.success(res.register(import_res))

    if self.current_tok.matches(TT_KEYWORD, 'return'):
      res.register_advancement()
      self.advance()

      expr = res.try_register(self.expr())
      if not expr:
        self.reverse(res.to_reverse_count)
      return res.success(ReturnNode(expr, pos_start, self.current_tok.pos_start.copy()))

    if self.current_tok.matches(TT_KEYWORD, 'continue'):
      res.register_advancement()
      self.advance()
      return res.success(ContinueNode(pos_start, self.current_tok.pos_start.copy()))

    if self.current_tok.matches(TT_KEYWORD, 'break'):
      res.register_advancement()
      self.advance()
      return res.success(BreakNode(pos_start, self.current_tok.pos_start.copy()))

    expr = res.register(self.expr())
    if res.error:
      return res.failure(InvalidSyntaxError(
        self.current_tok.pos_start, self.current_tok.pos_end,
        "Expected 'return', 'continue', 'break', 'initiate', 'if', 'for', 'while', 'function', int, float, identifier, '+', '-', '(', '[' or 'not'"
      ))
    return res.success(expr)

  def import_statement(self):
    res = ParseResult()
    pos_start = self.current_tok.pos_start.copy()

    if not self.current_tok.matches(TT_KEYWORD, 'import'):
        return res.failure(InvalidSyntaxError(
            pos_start, self.current_tok.pos_end,
            "Expected 'import' keyword"
        ))

    res.register_advancement()
    self.advance()  # Consume 'import'

    imports = []
    
    # Handle named imports {x, y, z}
    if self.current_tok.type == TT_LBRACE:
        res.register_advancement()
        self.advance()  # Consume '{'

        while self.current_tok.type != TT_RBRACE:
            if self.current_tok.type != TT_IDENTIFIER:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected identifier in import list"
                ))

            name = self.current_tok.value
            res.register_advancement()
            self.advance()

            # Handle 'as' alias
            alias = name
            if self.current_tok.matches(TT_KEYWORD, 'as'):
                res.register_advancement()
                self.advance()
                
                if self.current_tok.type != TT_IDENTIFIER:
                    return res.failure(InvalidSyntaxError(
                        self.current_tok.pos_start, self.current_tok.pos_end,
                        "Expected identifier after 'as'"
                    ))
                
                alias = self.current_tok.value
                res.register_advancement()
                self.advance()

            imports.append((name, alias))

            # Handle comma separator
            if self.current_tok.type == TT_COMMA:
                res.register_advancement()
                self.advance()

        if self.current_tok.type != TT_RBRACE:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected '}' to close import list"
            ))

        res.register_advancement()
        self.advance()  # Consume '}'
    else:
        # Handle default import (single identifier)
        if self.current_tok.type != TT_IDENTIFIER:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected identifier after 'import'"
            ))

        name = self.current_tok.value
        res.register_advancement()
        self.advance()
        imports.append((name, name))

    # Expect 'from' keyword
    if not self.current_tok.matches(TT_KEYWORD, 'from'):
        return res.failure(InvalidSyntaxError(
            self.current_tok.pos_start, self.current_tok.pos_end,
            "Expected 'from' after import specifiers"
        ))

    res.register_advancement()
    self.advance()

    # Expect module path string
    if self.current_tok.type != TT_STRING:
        return res.failure(InvalidSyntaxError(
            self.current_tok.pos_start, self.current_tok.pos_end,
            "Expected module path string"
        ))

    module_path = self.current_tok.value
    res.register_advancement()
    self.advance()

    return res.success(ImportNode(imports, module_path, pos_start, self.current_tok.pos_end.copy()))  

  def expr(self):
    res = ParseResult()

    if self.current_tok.matches(TT_KEYWORD, 'initiate'):
      res.register_advancement()
      self.advance()

      if self.current_tok.type != TT_IDENTIFIER:
        return res.failure(InvalidSyntaxError(
          self.current_tok.pos_start, self.current_tok.pos_end,
          "Expected identifier"
        ))

      var_name = self.current_tok
      res.register_advancement()
      self.advance()

      if self.current_tok.type != TT_EQ:
        return res.failure(InvalidSyntaxError(
          self.current_tok.pos_start, self.current_tok.pos_end,
          "Expected '='"
        ))

      res.register_advancement()
      self.advance()
      expr = res.register(self.expr())
      if res.error: return res
      return res.success(VarAssignNode(var_name, expr))

    node = res.register(self.bin_op(self.comp_expr, ((TT_KEYWORD, 'and'), (TT_KEYWORD, 'or'))))

    if res.error:
      return res.failure(InvalidSyntaxError(
        self.current_tok.pos_start, self.current_tok.pos_end,
        "Expected 'initiate', 'if', 'for', 'while', 'function', int, float, identifier, '+', '-', '(', '[' or 'not'"
      ))

    return res.success(node)

  def comp_expr(self):
    res = ParseResult()

    if self.current_tok.matches(TT_KEYWORD, 'not'):
      op_tok = self.current_tok
      res.register_advancement()
      self.advance()

      node = res.register(self.comp_expr())
      if res.error: return res
      return res.success(UnaryOpNode(op_tok, node))

    node = res.register(self.bin_op(self.arith_expr, (TT_EE, TT_NE, TT_LT, TT_GT, TT_LTE, TT_GTE)))

    if res.error:
      return res.failure(InvalidSyntaxError(
        self.current_tok.pos_start, self.current_tok.pos_end,
        "Expected int, float, identifier, '+', '-', '(', '[', 'IF', 'FOR', 'WHILE', 'FUN' or 'NOT'"
      ))

    return res.success(node)

  def arith_expr(self):
    return self.bin_op(self.term, (TT_PLUS, TT_MINUS))

  def term(self):
    return self.bin_op(self.factor, (TT_MUL, TT_DIV, TT_MOD))

  def factor(self):
    res = ParseResult()
    tok = self.current_tok

    if tok.type in (TT_PLUS, TT_MINUS):
      res.register_advancement()
      self.advance()
      factor = res.register(self.factor())
      if res.error: return res
      return res.success(UnaryOpNode(tok, factor))

    return self.power()

  def power(self):
    return self.bin_op(self.call, (TT_POW, ), self.factor)

  def call(self):
    res = ParseResult()
    atom = res.register(self.atom())
    if res.error: return res

    if self.current_tok.type == TT_LPAREN:
      res.register_advancement()
      self.advance()
      arg_nodes = []

      if self.current_tok.type == TT_RPAREN:
        res.register_advancement()
        self.advance()
      else:
        arg_nodes.append(res.register(self.expr()))
        if res.error:
          return res.failure(InvalidSyntaxError(
            self.current_tok.pos_start, self.current_tok.pos_end,
            "Expected ')', 'initiate', 'if', 'for', 'while', 'function', int, float, identifier, '+', '-', '(', '[' or 'not'"
          ))

        while self.current_tok.type == TT_COMMA:
          res.register_advancement()
          self.advance()

          arg_nodes.append(res.register(self.expr()))
          if res.error: return res

        if self.current_tok.type != TT_RPAREN:
          return res.failure(InvalidSyntaxError(
            self.current_tok.pos_start, self.current_tok.pos_end,
            f"Expected ',' or ')'"
          ))

        res.register_advancement()
        self.advance()
      return res.success(CallNode(atom, arg_nodes))
    return res.success(atom)

  def atom(self):
    res = ParseResult()
    tok = self.current_tok

    if tok.type in (TT_INT, TT_FLOAT):
      res.register_advancement()
      self.advance()
      return res.success(NumberNode(tok))

    elif tok.type == TT_STRING:
      res.register_advancement()
      self.advance()
      return res.success(StringNode(tok))

    elif tok.type == TT_IDENTIFIER:
      res.register_advancement()
      self.advance()
      return res.success(VarAccessNode(tok))

    elif tok.type == TT_LPAREN:
      res.register_advancement()
      self.advance()
      expr = res.register(self.expr())
      if res.error: return res
      if self.current_tok.type == TT_RPAREN:
        res.register_advancement()
        self.advance()
        return res.success(expr)
      else:
        return res.failure(InvalidSyntaxError(
          self.current_tok.pos_start, self.current_tok.pos_end,
          "Expected ')'"
        ))

    elif tok.type == TT_LSQUARE:
      list_expr = res.register(self.list_expr())
      if res.error: return res
      return res.success(list_expr)

    elif tok.matches(TT_KEYWORD, 'if'):
      if_expr = res.register(self.if_expr())
      if res.error: return res
      return res.success(if_expr)

    elif tok.matches(TT_KEYWORD, 'for'):
      for_expr = res.register(self.for_expr())
      if res.error: return res
      return res.success(for_expr)

    elif tok.matches(TT_KEYWORD, 'while'):
      while_expr = res.register(self.while_expr())
      if res.error: return res
      return res.success(while_expr)

    elif tok.matches(TT_KEYWORD, 'function'):
      func_def = res.register(self.func_def())
      if res.error: return res
      return res.success(func_def)
    
    elif tok.matches(TT_KEYWORD, 'fuck_around'):
        try_expr = res.register(self.try_expr())
        if res.error: return res
        return res.success(try_expr)
      
    elif tok.matches(TT_KEYWORD, 'async'):
        res.register_advancement()
        self.advance()
        
        expr = res.register(self.expr())
        if res.error: return res
        
        return res.success(AsyncNode(expr))
        
    elif tok.matches(TT_KEYWORD, 'await'):
        res.register_advancement()
        self.advance()
        
        expr = res.register(self.expr())
        if res.error: return res
        
        return res.success(AwaitNode(expr))
      
    elif tok.matches(TT_KEYWORD, 'sleep'):
        res.register_advancement()
        self.advance()
        
        if self.current_tok.type != TT_LPAREN:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected '(' after 'sleep'"
            ))
            
        res.register_advancement()
        self.advance()
        
        duration = res.register(self.expr())
        if res.error: return res
        
        if self.current_tok.type != TT_RPAREN:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected ')' after sleep duration"
            ))
            
        res.register_advancement()
        self.advance()
        
        return res.success(SleepNode(duration, tok.pos_start, self.current_tok.pos_end))

    return res.failure(InvalidSyntaxError(
      tok.pos_start, tok.pos_end,
      "Expected int, float, identifier, '+', '-', '(', '[', if', 'for', 'while', 'function'"
    ))
  
  def try_expr(self):
    res = ParseResult()
    pos_start = self.current_tok.pos_start.copy()

    if not self.current_tok.matches(TT_KEYWORD, 'fuck_around'):
        return res.failure(InvalidSyntaxError(
            self.current_tok.pos_start, self.pos_end,
            f"Expected 'fuck_around'"
        ))

    res.register_advancement()
    self.advance()

    # Check for multi-line version (with THEN)
    if self.current_tok.matches(TT_KEYWORD, 'THEN'):
        res.register_advancement()
        self.advance()

        if self.current_tok.type == TT_NEWLINE:
            res.register_advancement()
            self.advance()

            try_body = res.register(self.statements())
            if res.error: return res

            if not self.current_tok.matches(TT_KEYWORD, 'find_out'):
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.pos_end,
                    f"Expected 'find_out'"
                ))

            res.register_advancement()
            self.advance()

            if self.current_tok.type != TT_LPAREN:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.pos_end,
                    f"Expected '('"
                ))

            res.register_advancement()
            self.advance()

            if self.current_tok.type != TT_IDENTIFIER:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.pos_end,
                    f"Expected identifier"
                ))

            catch_var = self.current_tok
            res.register_advancement()
            self.advance()

            if self.current_tok.type != TT_RPAREN:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.pos_end,
                    f"Expected ')'"
                ))

            res.register_advancement()
            self.advance()

            if self.current_tok.matches(TT_KEYWORD, 'THEN'):
                res.register_advancement()
                self.advance()

                if self.current_tok.type == TT_NEWLINE:
                    res.register_advancement()
                    self.advance()

                    catch_body = res.register(self.statements())
                    if res.error: return res

                    if not self.current_tok.matches(TT_KEYWORD, 'END'):
                        return res.failure(InvalidSyntaxError(
                            self.current_tok.pos_start, self.pos_end,
                            f"Expected 'END'"
                        ))

                    res.register_advancement()
                    self.advance()
                else:
                    catch_body = res.register(self.statement())
                    if res.error: return res
            else:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.pos_end,
                    f"Expected 'THEN'"
                ))

            return res.success(TryNode(
                try_body,
                catch_var,
                catch_body,
                pos_start,
                self.current_tok.pos_end.copy()
            ))
    
    # Single-line version (without THEN)
    try_body = res.register(self.statement())
    if res.error: return res

    if not self.current_tok.matches(TT_KEYWORD, 'find_out'):
        return res.failure(InvalidSyntaxError(
            self.current_tok.pos_start, self.pos_end,
            f"Expected 'find_out'"
        ))

    res.register_advancement()
    self.advance()

    if self.current_tok.type != TT_LPAREN:
        return res.failure(InvalidSyntaxError(
            self.current_tok.pos_start, self.pos_end,
            f"Expected '('"
        ))

    res.register_advancement()
    self.advance()

    if self.current_tok.type != TT_IDENTIFIER:
        return res.failure(InvalidSyntaxError(
            self.current_tok.pos_start, self.pos_end,
            f"Expected identifier"
        ))

    catch_var = self.current_tok
    res.register_advancement()
    self.advance()

    if self.current_tok.type != TT_RPAREN:
        return res.failure(InvalidSyntaxError(
            self.current_tok.pos_start, self.pos_end,
            f"Expected ')'"
        ))

    res.register_advancement()
    self.advance()

    catch_body = res.register(self.statement())
    if res.error: return res

    return res.success(TryNode(
        try_body,
        catch_var,
        catch_body,
        pos_start,
        self.current_tok.pos_end.copy()
    ))

  def list_expr(self):
    res = ParseResult()
    element_nodes = []
    pos_start = self.current_tok.pos_start.copy()

    if self.current_tok.type != TT_LSQUARE:
      return res.failure(InvalidSyntaxError(
        self.current_tok.pos_start, self.current_tok.pos_end,
        f"Expected '['"
      ))

    res.register_advancement()
    self.advance()

    if self.current_tok.type == TT_RSQUARE:
      res.register_advancement()
      self.advance()
    else:
      element_nodes.append(res.register(self.expr()))
      if res.error:
        return res.failure(InvalidSyntaxError(
          self.current_tok.pos_start, self.current_tok.pos_end,
          "Expected ']', 'initiate', 'if', 'for', 'while', 'function', int, float, identifier, '+', '-', '(', '[' or 'not'"
        ))

      while self.current_tok.type == TT_COMMA:
        res.register_advancement()
        self.advance()

        element_nodes.append(res.register(self.expr()))
        if res.error: return res

      if self.current_tok.type != TT_RSQUARE:
        return res.failure(InvalidSyntaxError(
          self.current_tok.pos_start, self.current_tok.pos_end,
          f"Expected ',' or ']'"
        ))

      res.register_advancement()
      self.advance()

    return res.success(ListNode(
      element_nodes,
      pos_start,
      self.current_tok.pos_end.copy()
    ))

  def if_expr(self):
    res = ParseResult()
    all_cases = res.register(self.if_expr_cases('if'))
    if res.error: return res
    cases, else_case = all_cases
    return res.success(IfNode(cases, else_case))

  def if_expr_b(self):
    return self.if_expr_cases('elif')

  def if_expr_c(self):
    res = ParseResult()
    else_case = None

    if self.current_tok.matches(TT_KEYWORD, 'else'):
        res.register_advancement()
        self.advance()

        # Make THEN optional for else clause too
        if self.current_tok.matches(TT_KEYWORD, 'THEN'):
            res.register_advancement()
            self.advance()

        if self.current_tok.type == TT_NEWLINE:
            res.register_advancement()
            self.advance()

            statements = res.register(self.statements())
            if res.error: return res
            else_case = (statements, True)

            if self.current_tok.matches(TT_KEYWORD, 'END'):
                res.register_advancement()
                self.advance()
            else:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected 'END'"
                ))
        else:
            expr = res.register(self.statement())
            if res.error: return res
            else_case = (expr, False)

    return res.success(else_case)

  def if_expr_b_or_c(self):
    res = ParseResult()
    cases, else_case = [], None

    if self.current_tok.matches(TT_KEYWORD, 'elif'):
        all_cases = res.register(self.if_expr_b())
        if res.error: return res
        cases, else_case = all_cases
    else:
        else_case = res.register(self.if_expr_c())
        if res.error: return res

    return res.success((cases, else_case))

  def if_expr_cases(self, case_keyword):
    res = ParseResult()
    cases = []
    else_case = None

    if not self.current_tok.matches(TT_KEYWORD, case_keyword):
        return res.failure(InvalidSyntaxError(
            self.current_tok.pos_start, self.current_tok.pos_end,
            f"Expected '{case_keyword}'"
        ))

    res.register_advancement()
    self.advance()

    condition = res.register(self.expr())
    if res.error: return res

    # Changed this part to make THEN optional for single-line if statements
    if self.current_tok.matches(TT_KEYWORD, 'THEN'):
        res.register_advancement()
        self.advance()

    if self.current_tok.type == TT_NEWLINE:
        # Multi-line case
        res.register_advancement()
        self.advance()

        statements = res.register(self.statements())
        if res.error: return res
        cases.append((condition, statements, True))

        if self.current_tok.matches(TT_KEYWORD, 'END'):
            res.register_advancement()
            self.advance()
        else:
            all_cases = res.register(self.if_expr_b_or_c())
            if res.error: return res
            new_cases, else_case = all_cases
            cases.extend(new_cases)
    else:
        # Single-line case
        expr = res.register(self.statement())
        if res.error: return res
        
        # Check if next token is elif/else on same line
        if self.current_tok.matches(TT_KEYWORD, 'elif') or self.current_tok.matches(TT_KEYWORD, 'else'):
            cases.append((condition, expr, False))
            all_cases = res.register(self.if_expr_b_or_c())
            if res.error: return res
            new_cases, else_case = all_cases
            cases.extend(new_cases)
        else:
            # Regular single-line if
            cases.append((condition, expr, False))

    return res.success((cases, else_case))

  def for_expr(self):
    res = ParseResult()

    if not self.current_tok.matches(TT_KEYWORD, 'for'):
      return res.failure(InvalidSyntaxError(
        self.current_tok.pos_start, self.current_tok.pos_end,
        f"Expected 'FOR'"
      ))

    res.register_advancement()
    self.advance()

    if self.current_tok.type != TT_IDENTIFIER:
      return res.failure(InvalidSyntaxError(
        self.current_tok.pos_start, self.current_tok.pos_end,
        f"Expected identifier"
      ))

    var_name = self.current_tok
    res.register_advancement()
    self.advance()

    if self.current_tok.type != TT_EQ:
      return res.failure(InvalidSyntaxError(
        self.current_tok.pos_start, self.current_tok.pos_end,
        f"Expected '='"
      ))

    res.register_advancement()
    self.advance()

    start_value = res.register(self.expr())
    if res.error: return res

    if not self.current_tok.matches(TT_KEYWORD, 'to'):
      return res.failure(InvalidSyntaxError(
        self.current_tok.pos_start, self.current_tok.pos_end,
        f"Expected 'TO'"
      ))

    res.register_advancement()
    self.advance()

    end_value = res.register(self.expr())
    if res.error: return res

    if self.current_tok.matches(TT_KEYWORD, 'step'):
      res.register_advancement()
      self.advance()

      step_value = res.register(self.expr())
      if res.error: return res
    else:
      step_value = None

    if not self.current_tok.matches(TT_KEYWORD, 'THEN'):
      return res.failure(InvalidSyntaxError(
        self.current_tok.pos_start, self.current_tok.pos_end,
        f"Expected 'THEN'"
      ))

    res.register_advancement()
    self.advance()

    if self.current_tok.type == TT_NEWLINE:
      res.register_advancement()
      self.advance()

      body = res.register(self.statements())
      if res.error: return res

      if not self.current_tok.matches(TT_KEYWORD, 'END'):
        return res.failure(InvalidSyntaxError(
          self.current_tok.pos_start, self.current_tok.pos_end,
          f"Expected 'END'"
        ))

      res.register_advancement()
      self.advance()

      return res.success(ForNode(var_name, start_value, end_value, step_value, body, True))

    body = res.register(self.statement())
    if res.error: return res

    return res.success(ForNode(var_name, start_value, end_value, step_value, body, False))

  def while_expr(self):
    res = ParseResult()

    if not self.current_tok.matches(TT_KEYWORD, 'while'):
      return res.failure(InvalidSyntaxError(
        self.current_tok.pos_start, self.current_tok.pos_end,
        f"Expected 'while'"
      ))

    res.register_advancement()
    self.advance()

    condition = res.register(self.expr())
    if res.error: return res

    if not self.current_tok.matches(TT_KEYWORD, 'THEN'):
      return res.failure(InvalidSyntaxError(
        self.current_tok.pos_start, self.current_tok.pos_end,
        f"Expected 'THEN'"
      ))

    res.register_advancement()
    self.advance()

    if self.current_tok.type == TT_NEWLINE:
      res.register_advancement()
      self.advance()

      body = res.register(self.statements())
      if res.error: return res

      if not self.current_tok.matches(TT_KEYWORD, 'END'):
        return res.failure(InvalidSyntaxError(
          self.current_tok.pos_start, self.current_tok.pos_end,
          f"Expected 'END'"
        ))

      res.register_advancement()
      self.advance()

      return res.success(WhileNode(condition, body, True))

    body = res.register(self.statement())
    if res.error: return res

    return res.success(WhileNode(condition, body, False))

  def func_def(self):
    res = ParseResult()

    if not self.current_tok.matches(TT_KEYWORD, 'function'):
      return res.failure(InvalidSyntaxError(
        self.current_tok.pos_start, self.current_tok.pos_end,
        f"Expected 'function'"
      ))

    res.register_advancement()
    self.advance()

    if self.current_tok.type == TT_IDENTIFIER:
      var_name_tok = self.current_tok
      res.register_advancement()
      self.advance()
      if self.current_tok.type != TT_LPAREN:
        return res.failure(InvalidSyntaxError(
          self.current_tok.pos_start, self.current_tok.pos_end,
          f"Expected '('"
        ))
    else:
      var_name_tok = None
      if self.current_tok.type != TT_LPAREN:
        return res.failure(InvalidSyntaxError(
          self.current_tok.pos_start, self.current_tok.pos_end,
          f"Expected identifier or '('"
        ))

    res.register_advancement()
    self.advance()
    arg_name_toks = []

    if self.current_tok.type == TT_IDENTIFIER:
      arg_name_toks.append(self.current_tok)
      res.register_advancement()
      self.advance()

      while self.current_tok.type == TT_COMMA:
        res.register_advancement()
        self.advance()

        if self.current_tok.type != TT_IDENTIFIER:
          return res.failure(InvalidSyntaxError(
            self.current_tok.pos_start, self.current_tok.pos_end,
            f"Expected identifier"
          ))

        arg_name_toks.append(self.current_tok)
        res.register_advancement()
        self.advance()

      if self.current_tok.type != TT_RPAREN:
        return res.failure(InvalidSyntaxError(
          self.current_tok.pos_start, self.current_tok.pos_end,
          f"Expected ',' or ')'"
        ))
    else:
      if self.current_tok.type != TT_RPAREN:
        return res.failure(InvalidSyntaxError(
          self.current_tok.pos_start, self.current_tok.pos_end,
          f"Expected identifier or ')'"
        ))

    res.register_advancement()
    self.advance()

    if self.current_tok.type == TT_ARROW:
      res.register_advancement()
      self.advance()

      body = res.register(self.expr())
      if res.error: return res

      return res.success(FuncDefNode(
        var_name_tok,
        arg_name_toks,
        body,
        True
      ))

    if self.current_tok.type != TT_NEWLINE:
      return res.failure(InvalidSyntaxError(
        self.current_tok.pos_start, self.current_tok.pos_end,
        f"Expected '->' or NEWLINE"
      ))

    res.register_advancement()
    self.advance()

    body = res.register(self.statements())
    if res.error: return res

    if not self.current_tok.matches(TT_KEYWORD, 'END'):
      return res.failure(InvalidSyntaxError(
        self.current_tok.pos_start, self.current_tok.pos_end,
        f"Expected 'END'"
      ))

    res.register_advancement()
    self.advance()

    return res.success(FuncDefNode(
      var_name_tok,
      arg_name_toks,
      body,
      False
    ))

  ###################################

  def bin_op(self, func_a, ops, func_b=None):
    if func_b == None:
      func_b = func_a

    res = ParseResult()
    left = res.register(func_a())
    if res.error: return res

    while self.current_tok.type in ops or (self.current_tok.type, self.current_tok.value) in ops:
      op_tok = self.current_tok
      res.register_advancement()
      self.advance()
      right = res.register(func_b())
      if res.error: return res
      left = BinOpNode(left, op_tok, right)

    return res.success(left)

#######################################
# RUNTIME RESULT
#######################################

class RTResult:
  def __init__(self):
    self.reset()

  def reset(self):
    self.value = None
    self.error = None
    self.func_return_value = None
    self.loop_should_continue = False
    self.loop_should_break = False

  def register(self, res):
    self.error = res.error
    self.func_return_value = res.func_return_value
    self.loop_should_continue = res.loop_should_continue
    self.loop_should_break = res.loop_should_break
    return res.value

  def success(self, value):
    self.reset()
    self.value = value
    return self

  def success_return(self, value):
    self.reset()
    self.func_return_value = value
    return self

  def success_continue(self):
    self.reset()
    self.loop_should_continue = True
    return self

  def success_break(self):
    self.reset()
    self.loop_should_break = True
    return self

  def failure(self, error):
    self.reset()
    self.error = error
    return self

  def should_return(self):
    # Note: this will allow you to continue and break outside the current function
    return (
      self.error or
      self.func_return_value or
      self.loop_should_continue or
      self.loop_should_break
    )

#######################################
# VALUES
#######################################

class Value:
  def __init__(self):
    self.set_pos()
    self.set_context()

  def set_pos(self, pos_start=None, pos_end=None):
    self.pos_start = pos_start
    self.pos_end = pos_end
    return self

  def set_context(self, context=None):
    self.context = context
    return self

  def added_to(self, other):
    return None, self.illegal_operation(other)

  def subbed_by(self, other):
    return None, self.illegal_operation(other)

  def multed_by(self, other):
    return None, self.illegal_operation(other)

  def dived_by(self, other):
    return None, self.illegal_operation(other)

  def powed_by(self, other):
    return None, self.illegal_operation(other)

  def get_comparison_eq(self, other):
    return None, self.illegal_operation(other)

  def get_comparison_ne(self, other):
    return None, self.illegal_operation(other)

  def get_comparison_lt(self, other):
    return None, self.illegal_operation(other)

  def get_comparison_gt(self, other):
    return None, self.illegal_operation(other)

  def get_comparison_lte(self, other):
    return None, self.illegal_operation(other)

  def get_comparison_gte(self, other):
    return None, self.illegal_operation(other)

  def anded_by(self, other):
    return None, self.illegal_operation(other)

  def ored_by(self, other):
    return None, self.illegal_operation(other)

  def notted(self, other):
    return None, self.illegal_operation(other)

  def execute(self, args):
    return RTResult().failure(self.illegal_operation())

  def copy(self):
    raise Exception('No copy method defined')

  def is_true(self):
    return False

  def illegal_operation(self, other=None):
    if not other: other = self
    return RTError(
      self.pos_start, other.pos_end,
      'Illegal operation',
      self.context
    )

class Number(Value):
  def __init__(self, value):
    super().__init__()
    self.value = value

  def added_to(self, other):
    if isinstance(other, Number):
      return Number(self.value + other.value).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)

  def subbed_by(self, other):
    if isinstance(other, Number):
      return Number(self.value - other.value).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)

  def multed_by(self, other):
    if isinstance(other, Number):
      return Number(self.value * other.value).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)

  def dived_by(self, other):
    if isinstance(other, Number):
      if other.value == 0:
        return None, RTError(
          other.pos_start, other.pos_end,
          'Division by zero',
          self.context
        )

      return Number(self.value / other.value).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)
    
  def moded_by(self, other):
    if isinstance(other, Number):
      if other.value == 0:
        return None, RTError(self.pos_start, other.pos_end, "Modulo by zero", self.context)
      return Number(self.value % other.value).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)


  def powed_by(self, other):
    if isinstance(other, Number):
      return Number(self.value ** other.value).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)

  def get_comparison_eq(self, other):
    if isinstance(other, Number):
      return Number(int(self.value == other.value)).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)

  def get_comparison_ne(self, other):
    if isinstance(other, Number):
      return Number(int(self.value != other.value)).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)

  def get_comparison_lt(self, other):
    if isinstance(other, Number):
      return Number(int(self.value < other.value)).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)

  def get_comparison_gt(self, other):
    if isinstance(other, Number):
      return Number(int(self.value > other.value)).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)

  def get_comparison_lte(self, other):
    if isinstance(other, Number):
      return Number(int(self.value <= other.value)).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)

  def get_comparison_gte(self, other):
    if isinstance(other, Number):
      return Number(int(self.value >= other.value)).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)

  def anded_by(self, other):
    if isinstance(other, Number):
      return Number(int(self.value and other.value)).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)

  def ored_by(self, other):
    if isinstance(other, Number):
      return Number(int(self.value or other.value)).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)

  def notted(self):
    return Number(1 if self.value == 0 else 0).set_context(self.context), None

  def copy(self):
    copy = Number(self.value)
    copy.set_pos(self.pos_start, self.pos_end)
    copy.set_context(self.context)
    return copy

  def is_true(self):
    return self.value != 0

  def __str__(self):
    return str(self.value)

  def __repr__(self):
    return str(self.value)

Number.null = Number(0)
Number.false = Number(0)
Number.true = Number(1)
Number.math_PI = Number(math.pi)

class String(Value):
  def __init__(self, value):
    super().__init__()
    self.value = value

  def added_to(self, other):
    if isinstance(other, (String, Number, ErrorValue)):
        return String(f"{self.value}{other}").set_context(self.context), None
    return None, Value.illegal_operation(self, other)

  def multed_by(self, other):
    if isinstance(other, Number):
      return String(self.value * other.value).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)

  def is_true(self):
    return len(self.value) > 0

  def copy(self):
    copy = String(self.value)
    copy.set_pos(self.pos_start, self.pos_end)
    copy.set_context(self.context)
    return copy

  def __str__(self):
    return self.value

  def __repr__(self):
    return f'"{self.value}"'

class List(Value):
  def __init__(self, elements):
    super().__init__()
    self.elements = elements

  def added_to(self, other):
    new_list = self.copy()
    new_list.elements.append(other)
    return new_list, None

  def subbed_by(self, other):
    if isinstance(other, Number):
      new_list = self.copy()
      try:
        new_list.elements.pop(other.value)
        return new_list, None
      except:
        return None, RTError(
          other.pos_start, other.pos_end,
          'Element at this index could not be removed from list because index is out of bounds',
          self.context
        )
    else:
      return None, Value.illegal_operation(self, other)

  def multed_by(self, other):
    if isinstance(other, List):
      new_list = self.copy()
      new_list.elements.extend(other.elements)
      return new_list, None
    else:
      return None, Value.illegal_operation(self, other)

  def dived_by(self, other):
    if isinstance(other, Number):
      try:
        return self.elements[other.value], None
      except:
        return None, RTError(
          other.pos_start, other.pos_end,
          'Element at this index could not be retrieved from list because index is out of bounds',
          self.context
        )
    else:
      return None, Value.illegal_operation(self, other)

  def copy(self):
    copy = List(self.elements)
    copy.set_pos(self.pos_start, self.pos_end)
    copy.set_context(self.context)
    return copy

  def __str__(self):
    return ", ".join([str(x) for x in self.elements])

  def __repr__(self):
    return f'[{", ".join([repr(x) for x in self.elements])}]'

class BaseFunction(Value):
  def __init__(self, name):
    super().__init__()
    self.name = name or "<anonymous>"

  def generate_new_context(self):
    new_context = Context(self.name, self.context, self.pos_start)
    new_context.symbol_table = SymbolTable(new_context.parent.symbol_table)
    return new_context

  def check_args(self, arg_names, args):
    res = RTResult()

    if len(args) > len(arg_names):
      return res.failure(RTError(
        self.pos_start, self.pos_end,
        f"{len(args) - len(arg_names)} too many args passed into {self}",
        self.context
      ))

    if len(args) < len(arg_names):
      return res.failure(RTError(
        self.pos_start, self.pos_end,
        f"{len(arg_names) - len(args)} too few args passed into {self}",
        self.context
      ))

    return res.success(None)

  def populate_args(self, arg_names, args, exec_ctx):
    for i in range(len(args)):
      arg_name = arg_names[i]
      arg_value = args[i]
      arg_value.set_context(exec_ctx)
      exec_ctx.symbol_table.set(arg_name, arg_value)

  def check_and_populate_args(self, arg_names, args, exec_ctx):
    res = RTResult()
    res.register(self.check_args(arg_names, args))
    if res.should_return(): return res
    self.populate_args(arg_names, args, exec_ctx)
    return res.success(None)
  
class ErrorValue(Value):
  def __init__(self, error):
    super().__init__()
    self.error = error
    # Add quick-access properties
    self.properties = {
      "message": String(f"{error.error_name}: {error.details}"),
      "line": Number(error.pos_start.ln + 1),
      "column": Number(error.pos_start.col + 1),
      "file": String(error.pos_start.fn)
    }
      
  def copy(self):
    copy = ErrorValue(self.error)
    copy.set_pos(self.pos_start, self.pos_end)
    copy.set_context(self.context)
    return copy
  
  def get_property(self, prop_name):
    if prop_name in self.properties:
        return self.properties[prop_name]
    return None

  def added_to(self, other):
    if isinstance(other, String):
        return String(f"{other.value}{self}").set_context(self.context), None
    return None, Value.illegal_operation(self, other)

  def __str__(self):
    # Include arrow pointers for better debugging
    error = self.error
    return (
      f"{error.error_name}: {error.details}\n"
      f"File {error.pos_start.fn}, line {error.pos_start.ln + 1}\n"
      f"{string_with_arrows(error.pos_start.ftxt, error.pos_start, error.pos_end)}"
    )

  def __repr__(self):
    return f"ErrorValue({self.error.error_name})"

class Function(BaseFunction):
  def __init__(self, name, body_node, arg_names, should_auto_return):
    super().__init__(name)
    self.body_node = body_node
    self.arg_names = arg_names
    self.should_auto_return = should_auto_return

  def execute(self, args):
    res = RTResult()
    interpreter = Interpreter()
    exec_ctx = self.generate_new_context()

    res.register(self.check_and_populate_args(self.arg_names, args, exec_ctx))
    if res.should_return(): return res

    value = res.register(interpreter.visit(self.body_node, exec_ctx))
    if res.should_return() and res.func_return_value == None: return res

    ret_value = (value if self.should_auto_return else None) or res.func_return_value or Number.null
    return res.success(ret_value)

  def copy(self):
    copy = Function(self.name, self.body_node, self.arg_names, self.should_auto_return)
    copy.set_context(self.context)
    copy.set_pos(self.pos_start, self.pos_end)
    return copy

  def __repr__(self):
    return f"<function {self.name}>"

class AsyncFunction(BaseFunction):
  def __init__(self, name, body_node, arg_names, should_auto_return):
    super().__init__(name)
    self.body_node = body_node
    self.arg_names = arg_names
    self.should_auto_return = should_auto_return
      
  def execute(self, args):
    res = RTResult()
    interpreter = Interpreter()
    exec_ctx = self.generate_new_context()
    
    res.register(self.check_and_populate_args(self.arg_names, args, exec_ctx))
    if res.should_return(): return res
    
    # Return a coroutine instead of executing immediately
    return res.success(AsyncCoroutine(self, exec_ctx))
      
  def copy(self):
    copy = AsyncFunction(self.name, self.body_node, self.arg_names, self.should_auto_return)
    copy.set_context(self.context)
    copy.set_pos(self.pos_start, self.pos_end)
    return copy
      
  def __repr__(self):
    return f"<async function {self.name}>"

class AsyncCoroutine(Value):
  def __init__(self, func, context):
    super().__init__()
    self.func = func
    self.context = context
      
  def execute(self):
    interpreter = Interpreter()
    value = interpreter.visit(self.func.body_node, self.context)
    if self.func.should_auto_return:
      return value
    return RTResult().success(Number.null)
      
  def copy(self):
    copy = AsyncCoroutine(self.func, self.context)
    copy.set_context(self.context)
    copy.set_pos(self.func.pos_start, self.func.pos_end)
    return copy
      
  def __repr__(self):
    return f"<coroutine {self.func.name}>"

class EventLoop:
    def __init__(self):
        self.tasks = queue.Queue()
        self.thread_pool = []
        self.max_threads = 4
        self.running = False
        
    def start(self):
        self.running = True
        for _ in range(self.max_threads):
            thread = threading.Thread(target=self._worker)
            thread.daemon = True
            thread.start()
            self.thread_pool.append(thread)
            
    def stop(self):
        self.running = False
        for thread in self.thread_pool:
            thread.join()
            
    def _worker(self):
        while self.running:
            try:
                task = self.tasks.get(timeout=0.1)
                if task:
                    task()
                self.tasks.task_done()
            except queue.Empty:
                continue
                
    def submit(self, coroutine, callback):
        def task():
            result = coroutine.execute()
            callback(result)
        self.tasks.put(task)

# Global event loop
event_loop = EventLoop()

class BuiltInFunction(BaseFunction):
  def __init__(self, name):
    super().__init__(name)

  def execute(self, args):
    res = RTResult()
    exec_ctx = self.generate_new_context()

    method_name = f'execute_{self.name}'
    method = getattr(self, method_name, self.no_visit_method)

    res.register(self.check_and_populate_args(method.arg_names, args, exec_ctx))
    if res.should_return(): return res

    return_value = res.register(method(exec_ctx))
    if res.should_return(): return res
    return res.success(return_value)
  
  def execute_run_async(self, exec_ctx):
        coroutine = exec_ctx.symbol_table.get("coroutine")
        callback = exec_ctx.symbol_table.get("callback")
        
        if not isinstance(coroutine, AsyncCoroutine):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "First argument must be a coroutine",
                exec_ctx
            ))
            
        if not isinstance(callback, BaseFunction):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Second argument must be a function",
                exec_ctx
            ))
            
        def cb(result):
            callback.execute([result.value])
            
        event_loop.submit(coroutine, cb)
        return RTResult().success(Number.null)
  execute_run_async.arg_names = ["coroutine", "callback"]

  def no_visit_method(self, node, context):
    raise Exception(f'No execute_{self.name} method defined')

  def copy(self):
    copy = BuiltInFunction(self.name)
    copy.set_context(self.context)
    copy.set_pos(self.pos_start, self.pos_end)
    return copy

  def __repr__(self):
    return f"<built-in function {self.name}>"

  #####################################

  # *************************************************************

  #####################################
  # CUSTOM IN-BUILT FUNCTIONS *********************************
  #####################################

  def execute_print(self, exec_ctx):
    print(str(exec_ctx.symbol_table.get('value')))
    return RTResult().success(Number.null)
  execute_print.arg_names = ['value']

  def execute_print_ret(self, exec_ctx):
    return RTResult().success(String(str(exec_ctx.symbol_table.get('value'))))
  execute_print_ret.arg_names = ['value']

  def execute_input(self, exec_ctx):
    text = input()
    return RTResult().success(String(text))
  execute_input.arg_names = []

  def execute_input_int(self, exec_ctx):
    while True:
      text = input()
      try:
        number = int(text)
        break
      except ValueError:
        print(f"'{text}' must be an integer. Try again!")
    return RTResult().success(Number(number))
  execute_input_int.arg_names = []

  def execute_clear(self, exec_ctx):
    os.system('cls' if os.name == 'nt' else 'cls')
    return RTResult().success(Number.null)
  execute_clear.arg_names = []

  def execute_is_number(self, exec_ctx):
    is_number = isinstance(exec_ctx.symbol_table.get("value"), Number)
    return RTResult().success(Number.true if is_number else Number.false)
  execute_is_number.arg_names = ["value"]

  def execute_is_string(self, exec_ctx):
    is_number = isinstance(exec_ctx.symbol_table.get("value"), String)
    return RTResult().success(Number.true if is_number else Number.false)
  execute_is_string.arg_names = ["value"]

  def execute_is_list(self, exec_ctx):
    is_number = isinstance(exec_ctx.symbol_table.get("value"), List)
    return RTResult().success(Number.true if is_number else Number.false)
  execute_is_list.arg_names = ["value"]

  def execute_is_function(self, exec_ctx):
    is_number = isinstance(exec_ctx.symbol_table.get("value"), BaseFunction)
    return RTResult().success(Number.true if is_number else Number.false)
  execute_is_function.arg_names = ["value"]

  def execute_append(self, exec_ctx):
    list_ = exec_ctx.symbol_table.get("list")
    value = exec_ctx.symbol_table.get("value")

    if not isinstance(list_, List):
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        "First argument must be list",
        exec_ctx
      ))

    list_.elements.append(value)
    return RTResult().success(Number.null)
  execute_append.arg_names = ["list", "value"]

  def execute_pop(self, exec_ctx):
    list_ = exec_ctx.symbol_table.get("list")
    index = exec_ctx.symbol_table.get("index")

    if not isinstance(list_, List):
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        "First argument must be list",
        exec_ctx
      ))

    if not isinstance(index, Number):
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        "Second argument must be number",
        exec_ctx
      ))

    try:
      element = list_.elements.pop(index.value)
    except:
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        'Element at this index could not be removed from list because index is out of bounds',
        exec_ctx
      ))
    return RTResult().success(element)
  execute_pop.arg_names = ["list", "index"]

  def execute_extend(self, exec_ctx):
    listA = exec_ctx.symbol_table.get("listA")
    listB = exec_ctx.symbol_table.get("listB")

    if not isinstance(listA, List):
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        "First argument must be list",
        exec_ctx
      ))

    if not isinstance(listB, List):
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        "Second argument must be list",
        exec_ctx
      ))

    listA.elements.extend(listB.elements)
    return RTResult().success(Number.null)
  execute_extend.arg_names = ["listA", "listB"]

  def execute_len(self, exec_ctx):
    list_ = exec_ctx.symbol_table.get("list")

    if not isinstance(list_, List):
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        "Argument must be list",
        exec_ctx
      ))

    return RTResult().success(Number(len(list_.elements)))
  execute_len.arg_names = ["list"]

  def execute_run(self, exec_ctx):
    fn = exec_ctx.symbol_table.get("fn")

    if not isinstance(fn, String):
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        "Second argument must be string",
        exec_ctx
      ))

    fn = fn.value

    try:
      with open(fn, "r") as f:
        script = f.read()
    except Exception as e:
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        f"Failed to load script \"{fn}\"\n" + str(e),
        exec_ctx
      ))

    _, error = run(fn, script)

    if error:
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        f"Failed to finish executing script \"{fn}\"\n" +
        error.as_string(),
        exec_ctx
      ))

    return RTResult().success(Number.null)
  execute_run.arg_names = ["fn"]

  # *************************************************************

  #####################################
  # EXTRA CUSTOM IN-BUILT FUNCTIONS *************************
  #####################################

  def execute_merge(self, exec_ctx):
    listA = exec_ctx.symbol_table.get("listA")
    listB = exec_ctx.symbol_table.get("listB")

    if not isinstance(listA, List) or not isinstance(listB, List):
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        "Both arguments must be lists",
        exec_ctx
      ))

    new_list = listA.copy()
    new_list.elements.extend(listB.elements)
    return RTResult().success(new_list)
  execute_merge.arg_names = ["listA", "listB"]

  def execute_pop(self, exec_ctx):
    list_ = exec_ctx.symbol_table.get("list")

    if not isinstance(list_, List):
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        "Argument must be list",
        exec_ctx
      ))

    if len(list_.elements) == 0:
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        "Cannot pop from empty list",
        exec_ctx
      ))

    list_.elements.pop()
    return RTResult().success(Number.null)
  execute_pop.arg_names = ["list"]

  def execute_remove(self, exec_ctx):
    list_ = exec_ctx.symbol_table.get("list")
    index = exec_ctx.symbol_table.get("index")

    if not isinstance(list_, List):
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        "First argument must be list",
        exec_ctx
      ))

    if not isinstance(index, Number):
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        "Second argument must be number",
        exec_ctx
      ))

    try:
        list_.elements.pop(index.value)
    except IndexError:
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        "Index out of bounds",
        exec_ctx
      ))
    return RTResult().success(Number.null)
  execute_remove.arg_names = ["list", "index"]

  def execute_update(self, exec_ctx):
    list_ = exec_ctx.symbol_table.get("list")
    index = exec_ctx.symbol_table.get("index")
    value = exec_ctx.symbol_table.get("value")

    if not isinstance(list_, List):
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        "First argument must be list",
        exec_ctx
      ))

    if not isinstance(index, Number):
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        "Second argument must be number",
        exec_ctx
      ))

    try:
      list_.elements[index.value] = value
    except IndexError:
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        "Index out of bounds",
        exec_ctx
      ))
    return RTResult().success(Number.null)
  execute_update.arg_names = ["list", "index", "value"]

  def execute_len(self, exec_ctx):
    list_ = exec_ctx.symbol_table.get("list")

    if not isinstance(list_, List):
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        "Argument must be list",
        exec_ctx
      ))

    return RTResult().success(Number(len(list_.elements)))
  execute_len.arg_names = ["list"]

  def execute_wipe(self, exec_ctx):
    list_ = exec_ctx.symbol_table.get("list")

    if not isinstance(list_, List):
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        "Argument must be list",
        exec_ctx
      ))

    list_.elements = []
    return RTResult().success(Number.null)
  execute_wipe.arg_names = ["list"]

  def execute_contains(self, exec_ctx):
    list_ = exec_ctx.symbol_table.get("list")
    element = exec_ctx.symbol_table.get("element")

    if not isinstance(list_, List):
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        "First argument must be list",
        exec_ctx
      ))

    found = any(
      element.value == el.value if isinstance(el, (Number, String)) else element == el
      for el in list_.elements
    )
    return RTResult().success(Number.true if found else Number.false)
  execute_contains.arg_names = ["list", "element"]

  def execute_reverse(self, exec_ctx):
    list_ = exec_ctx.symbol_table.get("list")

    if not isinstance(list_, List):
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        "Argument must be list",
        exec_ctx
      ))

    reversed_list = list_.copy()
    reversed_list.elements = reversed_list.elements[::-1]
    return RTResult().success(reversed_list)
  execute_reverse.arg_names = ["list"]

  def execute_sort(self, exec_ctx):
    list_ = exec_ctx.symbol_table.get("list")

    if not isinstance(list_, List):
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        "Argument must be list",
        exec_ctx
      ))

    try:
      sorted_list = list_.copy()
      sorted_list.elements = sorted(
        sorted_list.elements,
        key=lambda x: x.value if isinstance(x, (Number, String)) else str(x)
      )
      return RTResult().success(sorted_list)
    except TypeError:
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        "Cannot sort list with mixed types",
        exec_ctx
      ))
  execute_sort.arg_names = ["list"]

  def execute_sum(self, exec_ctx):
    list_ = exec_ctx.symbol_table.get("list")

    if not isinstance(list_, List):
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        "Argument must be list",
        exec_ctx
      ))

    total = 0
    for element in list_.elements:
      if not isinstance(element, Number):
        return RTResult().failure(RTError(
          self.pos_start, self.pos_end,
          "All elements must be numbers",
          exec_ctx
        ))
      total += element.value

    return RTResult().success(Number(total))
  execute_sum.arg_names = ["list"]

  def execute_average(self, exec_ctx):
    list_ = exec_ctx.symbol_table.get("list")

    if not isinstance(list_, List):
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        "Argument must be list",
        exec_ctx
      ))

    if len(list_.elements) == 0:
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        "Cannot calculate average of empty list",
        exec_ctx
      ))

    total = 0
    for element in list_.elements:
      if not isinstance(element, Number):
        return RTResult().failure(RTError(
          self.pos_start, self.pos_end,
          "All elements must be numbers",
          exec_ctx
        ))
      total += element.value

    return RTResult().success(Number(total / len(list_.elements)))
  execute_average.arg_names = ["list"]

  def execute_min(self, exec_ctx):
    list_ = exec_ctx.symbol_table.get("list")

    if not isinstance(list_, List):
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        "Argument must be list",
        exec_ctx
      ))

    if len(list_.elements) == 0:
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        "Cannot find min of empty list",
        exec_ctx
      ))

    min_val = None
    for element in list_.elements:
      if not isinstance(element, Number):
        return RTResult().failure(RTError(
          self.pos_start, self.pos_end,
          "All elements must be numbers",
          exec_ctx
        ))
      if min_val is None or element.value < min_val:
        min_val = element.value

    return RTResult().success(Number(min_val))
  execute_min.arg_names = ["list"]

  def execute_max(self, exec_ctx):
    list_ = exec_ctx.symbol_table.get("list")

    if not isinstance(list_, List):
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        "Argument must be list",
        exec_ctx
      ))

    if len(list_.elements) == 0:
      return RTResult().failure(RTError(
          self.pos_start, self.pos_end,
          "Cannot find max of empty list",
          exec_ctx
      ))

    max_val = None
    for element in list_.elements:
        if not isinstance(element, Number):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "All elements must be numbers",
                exec_ctx
            ))
        if max_val is None or element.value > max_val:
            max_val = element.value

    return RTResult().success(Number(max_val))
  execute_max.arg_names = ["list"]

  def execute_count(self, exec_ctx):
      list_ = exec_ctx.symbol_table.get("list")
      element = exec_ctx.symbol_table.get("element")

      if not isinstance(list_, List):
          return RTResult().failure(RTError(
              self.pos_start, self.pos_end,
              "First argument must be list",
              exec_ctx
          ))

      count = 0
      for el in list_.elements:
          if isinstance(element, (Number, String)) and isinstance(el, (Number, String)):
              if element.value == el.value:
                  count += 1
          elif element == el:
              count += 1

      return RTResult().success(Number(count))
  execute_count.arg_names = ["list", "element"]

  def execute_push(self, exec_ctx):
      list_ = exec_ctx.symbol_table.get("list")
      value = exec_ctx.symbol_table.get("value")

      if not isinstance(list_, List):
          return RTResult().failure(RTError(
              self.pos_start, self.pos_end,
              "First argument must be list",
              exec_ctx
          ))

      list_.elements.append(value)
      return RTResult().success(Number.null)
  execute_push.arg_names = ["list", "value"]

  #####################################
  # MATH METHODS
  #####################################

  def execute_abs(self, exec_ctx):
      x = exec_ctx.symbol_table.get("x")

      if not isinstance(x, Number):
          return RTResult().failure(RTError(
              self.pos_start, self.pos_end,
              "Argument must be number",
              exec_ctx
          ))

      return RTResult().success(Number(abs(x.value)))
  execute_abs.arg_names = ["x"]

  def execute_round(self, exec_ctx):
      x = exec_ctx.symbol_table.get("x")

      if not isinstance(x, Number):
          return RTResult().failure(RTError(
              self.pos_start, self.pos_end,
              "Argument must be number",
              exec_ctx
          ))

      return RTResult().success(Number(round(x.value)))
  execute_round.arg_names = ["x"]

  def execute_ceil(self, exec_ctx):
      x = exec_ctx.symbol_table.get("x")

      if not isinstance(x, Number):
          return RTResult().failure(RTError(
              self.pos_start, self.pos_end,
              "Argument must be number",
              exec_ctx
          ))

      return RTResult().success(Number(math.ceil(x.value)))
  execute_ceil.arg_names = ["x"]

  def execute_floor(self, exec_ctx):
      x = exec_ctx.symbol_table.get("x")

      if not isinstance(x, Number):
          return RTResult().failure(RTError(
              self.pos_start, self.pos_end,
              "Argument must be number",
              exec_ctx
          ))

      return RTResult().success(Number(math.floor(x.value)))
  execute_floor.arg_names = ["x"]

  def execute_sqrt(self, exec_ctx):
      x = exec_ctx.symbol_table.get("x")

      if not isinstance(x, Number):
          return RTResult().failure(RTError(
              self.pos_start, self.pos_end,
              "Argument must be number",
              exec_ctx
          ))

      if x.value < 0:
          return RTResult().failure(RTError(
              self.pos_start, self.pos_end,
              "Cannot take square root of negative number",
              exec_ctx
          ))

      return RTResult().success(Number(math.sqrt(x.value)))
  execute_sqrt.arg_names = ["x"]

  def execute_power(self, exec_ctx):
      x = exec_ctx.symbol_table.get("x")
      y = exec_ctx.symbol_table.get("y")

      if not isinstance(x, Number) or not isinstance(y, Number):
          return RTResult().failure(RTError(
              self.pos_start, self.pos_end,
              "Both arguments must be numbers",
              exec_ctx
          ))

      return RTResult().success(Number(x.value ** y.value))
  execute_power.arg_names = ["x", "y"]

  #####################################
  # GENERIC UTILITY METHODS
  #####################################

  def execute_type_of(self, exec_ctx):
      value = exec_ctx.symbol_table.get("value")
      
      if isinstance(value, Number):
          type_name = "number"
      elif isinstance(value, String):
          type_name = "string"
      elif isinstance(value, List):
          type_name = "list"
      elif isinstance(value, BaseFunction):
          type_name = "function"
      elif isinstance(value, ErrorValue):
          type_name = "error"
      else:
          type_name = "null"
          
      return RTResult().success(String(type_name))
  execute_type_of.arg_names = ["value"]

  def execute_str(self, exec_ctx):
      value = exec_ctx.symbol_table.get("value")
      return RTResult().success(String(str(value)))
  execute_str.arg_names = ["value"]

  def execute_int(self, exec_ctx):
      value = exec_ctx.symbol_table.get("value")

      if isinstance(value, String):
          try:
              num = int(value.value)
              return RTResult().success(Number(num))
          except ValueError:
              return RTResult().failure(RTError(
                  self.pos_start, self.pos_end,
                  "Could not convert string to integer",
                  exec_ctx
              ))
      elif isinstance(value, Number):
          return RTResult().success(Number(int(value.value)))
      else:
          return RTResult().failure(RTError(
              self.pos_start, self.pos_end,
              "Cannot convert to integer",
              exec_ctx
          ))
  execute_int.arg_names = ["value"]

  def execute_float(self, exec_ctx):
      value = exec_ctx.symbol_table.get("value")

      if isinstance(value, String):
          try:
              num = float(value.value)
              return RTResult().success(Number(num))
          except ValueError:
              return RTResult().failure(RTError(
                  self.pos_start, self.pos_end,
                  "Could not convert string to float",
                  exec_ctx
              ))
      elif isinstance(value, Number):
          return RTResult().success(Number(float(value.value)))
      else:
          return RTResult().failure(RTError(
              self.pos_start, self.pos_end,
              "Cannot convert to float",
              exec_ctx
          ))
  execute_float.arg_names = ["value"]

  #####################################
  # STRING METHODS
  #####################################

  def execute_upper(self, exec_ctx):
      string = exec_ctx.symbol_table.get("string")

      if not isinstance(string, String):
          return RTResult().failure(RTError(
              self.pos_start, self.pos_end,
              "Argument must be string",
              exec_ctx
          ))

      return RTResult().success(String(string.value.upper()))
  execute_upper.arg_names = ["string"]

  def execute_lower(self, exec_ctx):
      string = exec_ctx.symbol_table.get("string")

      if not isinstance(string, String):
          return RTResult().failure(RTError(
              self.pos_start, self.pos_end,
              "Argument must be string",
              exec_ctx
          ))

      return RTResult().success(String(string.value.lower()))
  execute_lower.arg_names = ["string"]

  def execute_strip(self, exec_ctx):
      string = exec_ctx.symbol_table.get("string")

      if not isinstance(string, String):
          return RTResult().failure(RTError(
              self.pos_start, self.pos_end,
              "Argument must be string",
              exec_ctx
          ))

      return RTResult().success(String(string.value.strip()))
  execute_strip.arg_names = ["string"]

  def execute_reverse_str(self, exec_ctx):
      string = exec_ctx.symbol_table.get("string")

      if not isinstance(string, String):
          return RTResult().failure(RTError(
              self.pos_start, self.pos_end,
              "Argument must be string",
              exec_ctx
          ))

      return RTResult().success(String(string.value[::-1]))
  execute_reverse_str.arg_names = ["string"]

  def execute_len_str(self, exec_ctx):
      string = exec_ctx.symbol_table.get("string")

      if not isinstance(string, String):
          return RTResult().failure(RTError(
              self.pos_start, self.pos_end,
              "Argument must be string",
              exec_ctx
          ))

      return RTResult().success(Number(len(string.value)))
  execute_len_str.arg_names = ["string"]

  #####################################
  # ALGORITHMIC UTILITIES
  #####################################

  def execute_is_prime(self, exec_ctx):
    n = exec_ctx.symbol_table.get("n")

    if not isinstance(n, Number):
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        "Argument must be number",
        exec_ctx
      ))

    if n.value <= 1:
      return RTResult().success(Number.false)
    if n.value <= 3:
      return RTResult().success(Number.true)
    if n.value % 2 == 0 or n.value % 3 == 0:
      return RTResult().success(Number.false)

    i = 5
    while i * i <= n.value:
      if n.value % i == 0 or n.value % (i + 2) == 0:
        return RTResult().success(Number.false)
      i += 6

    return RTResult().success(Number.true)
  execute_is_prime.arg_names = ["n"]

  def execute_unique(self, exec_ctx):
    list_ = exec_ctx.symbol_table.get("list")

    if not isinstance(list_, List):
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        "Argument must be list",
        exec_ctx
      ))

    seen = []
    unique_elements = []
    for element in list_.elements:
      if isinstance(element, (Number, String)):
        if element.value not in seen:
          seen.append(element.value)
          unique_elements.append(element)
      elif element not in seen:
        seen.append(element)
        unique_elements.append(element)

    new_list = List(unique_elements)
    return RTResult().success(new_list)
  execute_unique.arg_names = ["list"]

  def execute_shuffle(self, exec_ctx):
    list_ = exec_ctx.symbol_table.get("list")

    if not isinstance(list_, List):
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        "Argument must be list",
        exec_ctx
      ))

    shuffled = list_.copy()
    random.shuffle(shuffled.elements)
    return RTResult().success(shuffled)
  execute_shuffle.arg_names = ["list"]


#####################################
# EXTRA CUSTOM IN-BUILT FUNCTIONS *************************
#####################################

BuiltInFunction.print       = BuiltInFunction("print")
BuiltInFunction.print_ret   = BuiltInFunction("print_ret")
BuiltInFunction.input       = BuiltInFunction("input")
BuiltInFunction.input_int   = BuiltInFunction("input_int")
BuiltInFunction.clear       = BuiltInFunction("clear")
BuiltInFunction.is_number   = BuiltInFunction("is_number")
BuiltInFunction.is_string   = BuiltInFunction("is_string")
BuiltInFunction.is_list     = BuiltInFunction("is_list")
BuiltInFunction.is_function = BuiltInFunction("is_function")
BuiltInFunction.append      = BuiltInFunction("append")
BuiltInFunction.pop         = BuiltInFunction("pop")
BuiltInFunction.extend      = BuiltInFunction("extend")
BuiltInFunction.len					= BuiltInFunction("len")
BuiltInFunction.run					= BuiltInFunction("run")

#####################################
# CUSTOM IN-BUILT FUNCTIONS *********************************
#####################################

BuiltInFunction.merge       = BuiltInFunction("merge")
BuiltInFunction.pop         = BuiltInFunction("pop")
BuiltInFunction.remove      = BuiltInFunction("remove")
BuiltInFunction.update      = BuiltInFunction("update")
BuiltInFunction.len         = BuiltInFunction("len")
BuiltInFunction.wipe        = BuiltInFunction("wipe")
BuiltInFunction.contains    = BuiltInFunction("contains")
BuiltInFunction.reverse     = BuiltInFunction("reverse")
BuiltInFunction.sort        = BuiltInFunction("sort")
BuiltInFunction.sum         = BuiltInFunction("sum")
BuiltInFunction.average     = BuiltInFunction("average")
BuiltInFunction.min         = BuiltInFunction("min")
BuiltInFunction.max         = BuiltInFunction("max")
BuiltInFunction.count       = BuiltInFunction("count")
BuiltInFunction.push        = BuiltInFunction("push")
BuiltInFunction.abs         = BuiltInFunction("abs")
BuiltInFunction.round       = BuiltInFunction("round")
BuiltInFunction.ceil        = BuiltInFunction("ceil")
BuiltInFunction.floor       = BuiltInFunction("floor")
BuiltInFunction.sqrt        = BuiltInFunction("sqrt")
BuiltInFunction.power       = BuiltInFunction("power")
BuiltInFunction.type_of     = BuiltInFunction("type_of")
BuiltInFunction.str         = BuiltInFunction("str")
BuiltInFunction.int         = BuiltInFunction("int")
BuiltInFunction.float       = BuiltInFunction("float")
BuiltInFunction.upper       = BuiltInFunction("upper")
BuiltInFunction.lower       = BuiltInFunction("lower")
BuiltInFunction.strip       = BuiltInFunction("strip")
BuiltInFunction.reverse_str = BuiltInFunction("reverse_str")
BuiltInFunction.len_str     = BuiltInFunction("len_str")
BuiltInFunction.is_prime    = BuiltInFunction("is_prime")
BuiltInFunction.unique      = BuiltInFunction("unique")
BuiltInFunction.shuffle     = BuiltInFunction("shuffle")

#######################################
# CONTEXT
#######################################

class Context:
  def __init__(self, display_name, parent=None, parent_entry_pos=None):
    self.display_name = display_name
    self.parent = parent
    self.parent_entry_pos = parent_entry_pos
    self.symbol_table = None

#######################################
# SYMBOL TABLE
#######################################

class SymbolTable:
  def __init__(self, parent=None):
    self.symbols = {}
    self.parent = parent

  def get(self, name):
    value = self.symbols.get(name, None)
    if value == None and self.parent:
      return self.parent.get(name)
    return value

  def set(self, name, value):
    self.symbols[name] = value

  def remove(self, name):
    del self.symbols[name]

#######################################
# INTERPRETER
#######################################

class Interpreter:
  def visit(self, node, context):
    method_name = f'visit_{type(node).__name__}'
    method = getattr(self, method_name, self.no_visit_method)
    return method(node, context)

  def no_visit_method(self, node, context):
    raise Exception(f'No visit_{type(node).__name__} method defined')

  ###################################

  def visit_NumberNode(self, node, context):
    return RTResult().success(
      Number(node.tok.value).set_context(context).set_pos(node.pos_start, node.pos_end)
    )

  def visit_StringNode(self, node, context):
    return RTResult().success(
      String(node.tok.value).set_context(context).set_pos(node.pos_start, node.pos_end)
    )
  
  def visit_TryNode(self, node, context):
    res = RTResult()
    
    # Execute try block
    try_value = res.register(self.visit(node.try_body, context))
    
    # Only execute catch block if there was an error
    if res.error:
        error_value = ErrorValue(res.error).set_context(context)
        
        # Store the error object and its properties
        context.symbol_table.set(node.catch_var.value, error_value)
        for prop_name, prop_value in error_value.properties.items():
            context.symbol_table.set(f"{node.catch_var.value}_{prop_name}", prop_value)
        
        # Clear the error so we can execute the catch block
        res.error = None
        catch_value = res.register(self.visit(node.catch_body, context))
        if res.error: return res
        
        # Return the catch block's result
        return res.success(catch_value)
    
    # Return the try block's result if no error occurred
    return res.success(try_value)
  
  def visit_ListNode(self, node, context):
    res = RTResult()
    elements = []

    for element_node in node.element_nodes:
      elements.append(res.register(self.visit(element_node, context)))
      if res.should_return(): return res

    return res.success(
      List(elements).set_context(context).set_pos(node.pos_start, node.pos_end)
    )

  def visit_VarAccessNode(self, node, context):
    res = RTResult()
    var_name = node.var_name_tok.value
    value = context.symbol_table.get(var_name)

    if not value:
      return res.failure(RTError(
        node.pos_start, node.pos_end,
        f"'{var_name}' is not defined",
        context
      ))

    value = value.copy().set_pos(node.pos_start, node.pos_end).set_context(context)
    return res.success(value)

  def visit_VarAssignNode(self, node, context):
    res = RTResult()
    var_name = node.var_name_tok.value
    value = res.register(self.visit(node.value_node, context))
    if res.should_return(): return res

    context.symbol_table.set(var_name, value)
    return res.success(value)

  def visit_BinOpNode(self, node, context):
    res = RTResult()
    left = res.register(self.visit(node.left_node, context))
    if res.should_return(): return res
    right = res.register(self.visit(node.right_node, context))
    if res.should_return(): return res

    if node.op_tok.type == TT_PLUS:
      result, error = left.added_to(right)
      
    elif node.op_tok.type == TT_MINUS:
      result, error = left.subbed_by(right)
      
    elif node.op_tok.type == TT_MUL:
      result, error = left.multed_by(right)
      
    elif node.op_tok.type == TT_DIV:
      result, error = left.dived_by(right)
      
    elif node.op_tok.type == TT_MOD:
      result, error = left.moded_by(right)

    elif node.op_tok.type == TT_POW:
      result, error = left.powed_by(right)
      
    elif node.op_tok.type == TT_EE:
      result, error = left.get_comparison_eq(right)
      
    elif node.op_tok.type == TT_NE:
      result, error = left.get_comparison_ne(right)
      
    elif node.op_tok.type == TT_LT:
      result, error = left.get_comparison_lt(right)
      
    elif node.op_tok.type == TT_GT:
      result, error = left.get_comparison_gt(right)
      
    elif node.op_tok.type == TT_LTE:
      result, error = left.get_comparison_lte(right)
      
    elif node.op_tok.type == TT_GTE:
      result, error = left.get_comparison_gte(right)
      
    elif node.op_tok.matches(TT_KEYWORD, 'AND'):
      result, error = left.anded_by(right)
      
    elif node.op_tok.matches(TT_KEYWORD, 'OR'):
      result, error = left.ored_by(right)
      

    if error:
      return res.failure(error)
    else:
      return res.success(result.set_pos(node.pos_start, node.pos_end))

  def visit_UnaryOpNode(self, node, context):
    res = RTResult()
    number = res.register(self.visit(node.node, context))
    if res.should_return(): return res

    error = None

    if node.op_tok.type == TT_MINUS:
      number, error = number.multed_by(Number(-1))
    elif node.op_tok.matches(TT_KEYWORD, 'NOT'):
      number, error = number.notted()

    if error:
      return res.failure(error)
    else:
      return res.success(number.set_pos(node.pos_start, node.pos_end))

  def visit_IfNode(self, node, context):
    res = RTResult()

    for condition, expr, should_return_null in node.cases:
      condition_value = res.register(self.visit(condition, context))
      if res.should_return(): return res

      if condition_value.is_true():
        expr_value = res.register(self.visit(expr, context))
        if res.should_return(): return res
        return res.success(Number.null if should_return_null else expr_value)

    if node.else_case:
      expr, should_return_null = node.else_case
      expr_value = res.register(self.visit(expr, context))
      if res.should_return(): return res
      return res.success(Number.null if should_return_null else expr_value)

    return res.success(Number.null)

  def visit_ForNode(self, node, context):
    res = RTResult()
    elements = []

    start_value = res.register(self.visit(node.start_value_node, context))
    if res.should_return(): return res

    end_value = res.register(self.visit(node.end_value_node, context))
    if res.should_return(): return res

    if node.step_value_node:
      step_value = res.register(self.visit(node.step_value_node, context))
      if res.should_return(): return res
    else:
      step_value = Number(1)

    i = start_value.value

    if step_value.value >= 0:
      condition = lambda: i < end_value.value
    else:
      condition = lambda: i > end_value.value

    while condition():
      context.symbol_table.set(node.var_name_tok.value, Number(i))
      i += step_value.value

      value = res.register(self.visit(node.body_node, context))
      if res.should_return() and res.loop_should_continue == False and res.loop_should_break == False: return res

      if res.loop_should_continue:
        continue

      if res.loop_should_break:
        break

      elements.append(value)

    return res.success(
      Number.null if node.should_return_null else
      List(elements).set_context(context).set_pos(node.pos_start, node.pos_end)
    )

  def visit_WhileNode(self, node, context):
    res = RTResult()
    elements = []

    while True:
      condition = res.register(self.visit(node.condition_node, context))
      if res.should_return(): return res

      if not condition.is_true():
        break

      value = res.register(self.visit(node.body_node, context))
      if res.should_return() and res.loop_should_continue == False and res.loop_should_break == False: return res

      if res.loop_should_continue:
        continue

      if res.loop_should_break:
        break

      elements.append(value)

    return res.success(
      Number.null if node.should_return_null else
      List(elements).set_context(context).set_pos(node.pos_start, node.pos_end)
    )

  def visit_FuncDefNode(self, node, context):
    res = RTResult()

    func_name = node.var_name_tok.value if node.var_name_tok else None
    body_node = node.body_node
    arg_names = [arg_name.value for arg_name in node.arg_name_toks]
    func_value = Function(func_name, body_node, arg_names, node.should_auto_return).set_context(context).set_pos(node.pos_start, node.pos_end)

    if node.var_name_tok:
      context.symbol_table.set(func_name, func_value)

    return res.success(func_value)

  def visit_CallNode(self, node, context):
    res = RTResult()
    args = []

    value_to_call = res.register(self.visit(node.node_to_call, context))
    if res.should_return(): return res
    value_to_call = value_to_call.copy().set_pos(node.pos_start, node.pos_end)

    for arg_node in node.arg_nodes:
      args.append(res.register(self.visit(arg_node, context)))
      if res.should_return(): return res

    return_value = res.register(value_to_call.execute(args))
    if res.should_return(): return res
    return_value = return_value.copy().set_pos(node.pos_start, node.pos_end).set_context(context)
    return res.success(return_value)

  def visit_ReturnNode(self, node, context):
    res = RTResult()

    if node.node_to_return:
      value = res.register(self.visit(node.node_to_return, context))
      if res.should_return(): return res
    else:
      value = Number.null

    return res.success_return(value)

  def visit_ContinueNode(self, node, context):
    return RTResult().success_continue()

  def visit_BreakNode(self, node, context):
    return RTResult().success_break()

  def visit_ImportNode(self, node, context):
    res = RTResult()
    module_path = node.module_path
    
    try:
        # Try to load the module
        with open(module_path + ".txt", "r") as f:  # Assuming .txt extension for modules
            module_code = f.read()
        
        # Run the module in a new context
        module_context = Context(f"<module {module_path}>", parent=context)
        module_context.symbol_table = SymbolTable(global_symbol_table)
        
        # Execute module code
        _, error = run(module_path, module_code)
        if error:
            return res.failure(error)
        
        # Import the specified symbols into current context
        for name, alias in node.imports:
            value = module_context.symbol_table.get(name)
            if not value:
                return res.failure(RTError(
                    node.pos_start, node.pos_end,
                    f"Cannot import '{name}' - not found in module",
                    context
                ))
            context.symbol_table.set(alias, value)
        
        return res.success(Number.null)
    
    except FileNotFoundError:
        return res.failure(RTError(
            node.pos_start, node.pos_end,
            f"Module '{module_path}' not found",
            context
        ))
    except Exception as e:
        return res.failure(RTError(
            node.pos_start, node.pos_end,
            f"Failed to import module: {str(e)}",
            context
        ))

  def visit_AsyncNode(self, node, context):
    res = RTResult()
    value = res.register(self.visit(node.node, context))
    if res.error: return res
    
    # If it's a function, make it async
    if isinstance(value, Function):
        async_func = AsyncFunction(value.name, value.body_node, value.arg_names, value.should_auto_return)
        async_func.set_context(value.context)
        async_func.set_pos(value.pos_start, value.pos_end)
        return res.success(async_func)
    
    # Otherwise wrap in a coroutine that immediately resolves
    return res.success(AsyncCoroutine(
        Function("<anonymous>", node.node, [], True).set_context(context),
        context
    ))

  def visit_AwaitNode(self, node, context):
      res = RTResult()
      value = res.register(self.visit(node.node, context))
      if res.error: return res
      
      if not isinstance(value, AsyncCoroutine):
          return res.failure(RTError(
              node.pos_start, node.pos_end,
              "Can only await a coroutine",
              context
          ))
      
      # In a real implementation, this would yield to the event loop
      # For simplicity, we'll just execute it directly here
      return value.execute()

  def visit_SleepNode(self, node, context):
      res = RTResult()
      duration = res.register(self.visit(node.duration_node, context))
      if res.error: return res
      
      if not isinstance(duration, Number):
          return res.failure(RTError(
              node.pos_start, node.pos_end,
              "Sleep duration must be a number",
              context
          ))
      
      # Simple synchronous sleep for now
      # In a real async implementation, this would be non-blocking
      import time
      time.sleep(duration.value)
      
      return res.success(Number.null)



#######################################
# RUN
#######################################

# INSTANCE OF SYMBOL TREE
global_symbol_table = SymbolTable()

# BOOLEANS & NULL
global_symbol_table.set("Null", Number.null)
global_symbol_table.set("False", Number.false)
global_symbol_table.set("True", Number.true)

# CONSTANTS
global_symbol_table.set("MATH_PI", Number.math_PI)

# IN-BUILT FUNCTIONS
global_symbol_table.set("echo", BuiltInFunction.print)
global_symbol_table.set("echo_ret", BuiltInFunction.print_ret)
global_symbol_table.set("listen", BuiltInFunction.input)
global_symbol_table.set("listen_int", BuiltInFunction.input_int)
global_symbol_table.set("die", BuiltInFunction.clear)
global_symbol_table.set("die", BuiltInFunction.clear)
global_symbol_table.set("is_numeric", BuiltInFunction.is_number)
global_symbol_table.set("is_string", BuiltInFunction.is_string)
global_symbol_table.set("is_list", BuiltInFunction.is_list)
global_symbol_table.set("is_function", BuiltInFunction.is_function)
global_symbol_table.set("append", BuiltInFunction.append)
global_symbol_table.set("pop", BuiltInFunction.pop)
global_symbol_table.set("extend", BuiltInFunction.extend)
global_symbol_table.set("len", BuiltInFunction.len)
global_symbol_table.set("awake", BuiltInFunction.run)


# EXTRA IN-BUILT FUNCTIONS
global_symbol_table.set("merge", BuiltInFunction.merge)
global_symbol_table.set("pop", BuiltInFunction.pop)
global_symbol_table.set("remove", BuiltInFunction.remove)
global_symbol_table.set("update", BuiltInFunction.update)
global_symbol_table.set("len", BuiltInFunction.len)
global_symbol_table.set("wipe", BuiltInFunction.wipe)
global_symbol_table.set("contains", BuiltInFunction.contains)
global_symbol_table.set("reverse", BuiltInFunction.reverse)
global_symbol_table.set("sort", BuiltInFunction.sort)
global_symbol_table.set("sum", BuiltInFunction.sum)
global_symbol_table.set("average", BuiltInFunction.average)
global_symbol_table.set("min", BuiltInFunction.min)
global_symbol_table.set("max", BuiltInFunction.max)
global_symbol_table.set("count", BuiltInFunction.count)
global_symbol_table.set("push", BuiltInFunction.push)
global_symbol_table.set("abs", BuiltInFunction.abs)
global_symbol_table.set("round", BuiltInFunction.round)
global_symbol_table.set("ceil", BuiltInFunction.ceil)
global_symbol_table.set("floor", BuiltInFunction.floor)
global_symbol_table.set("sqrt", BuiltInFunction.sqrt)
global_symbol_table.set("power", BuiltInFunction.power)
global_symbol_table.set("type_of", BuiltInFunction.type_of)
global_symbol_table.set("str", BuiltInFunction.str)
global_symbol_table.set("int", BuiltInFunction.int)
global_symbol_table.set("float", BuiltInFunction.float)
global_symbol_table.set("upper", BuiltInFunction.upper)
global_symbol_table.set("lower", BuiltInFunction.lower)
global_symbol_table.set("strip", BuiltInFunction.strip)
global_symbol_table.set("reverse_str", BuiltInFunction.reverse_str)
global_symbol_table.set("len_str", BuiltInFunction.len_str)
global_symbol_table.set("is_prime", BuiltInFunction.is_prime)
global_symbol_table.set("unique", BuiltInFunction.unique)
global_symbol_table.set("shuffle", BuiltInFunction.shuffle)
global_symbol_table.set("run_async", BuiltInFunction("run_async"))

def run(fn, text):
  # Generate tokens
  lexer = Lexer(fn, text)
  tokens, error = lexer.make_tokens()
  if error: return None, error

  # Generate AST
  parser = Parser(tokens)
  ast = parser.parse()
  if ast.error: 
    return None, ast.error

  # Run program
  interpreter = Interpreter()
  context = Context('<program>')
  context.symbol_table = global_symbol_table
  result = interpreter.visit(ast.node, context)

  return result.value, result.error


def validate(text):
  lexer = Lexer('<stdin>', text)
  tokens, error = lexer.make_tokens()
  if error: 
    return None, error
  
  parser = Parser(tokens)
  ast = parser.parse()
  if ast.error: 
    return None, ast.error
  
  return "Build successful", None
