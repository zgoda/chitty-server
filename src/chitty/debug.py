from trio.abc import Instrument
from trio.lowlevel import Task


class TaskLogger(Instrument):
    """Simple instrumentation object that traces Trio task execution.
    """

    def task_scheduled(self, task: Task):
        print(f'task scheduled: {task.name}')

    def before_task_step(self, task: Task):
        print(f'before task step: {task.name}')

    def after_task_step(self, task: Task):
        print(f'after task step: {task.name}')
