from core.values import List, Number, RTError
from core.context import Context

class AlgoModule:
    # Sorting algorithms
    @staticmethod
    def bubble_sort(list_, context):
      if not isinstance(list_, List):
        return RTError(
          None, None,
          "Argument must be a list",
          context
        )
      
      elements = [x.value for x in list_.elements if isinstance(x, Number)]
      n = len(elements)
      
      for i in range(n):
        for j in range(0, n-i-1):
          if elements[j] > elements[j+1]:
            elements[j], elements[j+1] = elements[j+1], elements[j]
      
      return List([Number(x) for x in elements])

    @staticmethod
    def selection_sort(list_, context):
      if not isinstance(list_, List):
        return RTError(
          None, None,
          "Argument must be a list",
          context
        )
          
      elements = [x.value for x in list_.elements if isinstance(x, Number)]
      n = len(elements)
      
      for i in range(n):
        min_idx = i
        for j in range(i+1, n):
          if elements[j] < elements[min_idx]:
            min_idx = j
        elements[i], elements[min_idx] = elements[min_idx], elements[i]
      
      return List([Number(x) for x in elements])

    # Other sorting algorithms...
    # Searching algorithms...

# Export the module functions
exports = {
  "bubble_sort": AlgoModule.bubble_sort,
  "selection_sort": AlgoModule.selection_sort,
  # Add other functions...
}