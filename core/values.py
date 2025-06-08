import math
import os
import random
from error import *
from nodes import *


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
