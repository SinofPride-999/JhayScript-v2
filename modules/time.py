import time
from core.values import Number, String
from core.context import Context

class TimeModule:
  @staticmethod
  def now(context):
    return String(time.strftime("%Y-%m-%d %H:%M:%S"))
  
  @staticmethod
  def timestamp(context):
    return Number(time.time())
  
  @staticmethod
  def sleep(seconds, context):
    if not isinstance(seconds, Number):
      return RTError(
        None, None,
        "Argument must be a number",
        context
      )
    time.sleep(seconds.value)
    return Number.null

exports = {
  "now": TimeModule.now,
  "timestamp": TimeModule.timestamp,
  "sleep": TimeModule.sleep
}