import pywikibot
import typing
import queue
import threading
import time
import itertools
from disambig_basic import disambig_linkshere_action, NoneProcess


class Task:
    def __init__(self, func: typing.Callable, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs
    
    def call(self):
        return self.func(*self.args, **self.kwargs)

    def __str__(self):
        return self.func.__name__ + '(' + ', '.join(itertools.chain((repr(a) for a in self.args), (k + '=' + repr(w) for k, w in self.kwargs))) + ')'


def process_print(*args, **kwargs):
    # print("process", *args, **kwargs)
    pass


class TaskProcess(threading.Thread, NoneProcess):
    def __init__(self):
        process_print("init")
        threading.Thread.__init__(self)
        self.tasks: queue.Queue[Task] = queue.Queue()
        self.task_lock: threading.Lock = threading.Lock()
        self.waiting: bool = False
        self.redos: queue.Queue[pywikibot.Page] = queue.Queue()
        self.redo_lock = threading.Lock()

    def add(self, func: typing.Callable, *args, **kwargs):
        task = Task(func, *args, **kwargs)
        process_print('add:', task)
        self.task_lock.acquire()
        self.tasks.put(task)
        self.task_lock.release()

    def print(self, *args, **kwargs):
        process_print("print:", args, kwargs)
        self.add(print, *args, **kwargs)

    def action(self, *args, **kwargs):
        process_print("action:", args, kwargs)
        self.add(disambig_linkshere_action, *args, **kwargs)

    def run(self):
        process_print("before running")
        empty: bool = True
        quited: bool = False
        while (not empty or not self.waiting) and not quited:
            process_print("running")
            self.task_lock.acquire()
            if not self.tasks.empty():
                empty = True
                task = self.tasks.get()
                self.task_lock.release()
                process_print('call:', task)
                ret = task.call()
                if ret == "redo":
                    self.redo_lock.acquire()
                    self.redos.put(task.kwargs.get("disambig", task.args[0]))
                    self.redo_lock.release()
                elif ret == "quit":
                    quited = True
                    exit(0)
            else:
                empty = False
                self.task_lock.release()
                time.sleep(1)

    def wait(self):
        process_print('wait')
        self.waiting = True
        self.join()
    
    def no_redo(self) -> bool:
        self.redo_lock.acquire()
        ret = self.redos.empty()
        self.redo_lock.release()
        return ret
    
    def gen_redo(self):
        self.redo_lock.acquire()
        while not self.redos.empty():
            redo = self.redos.get()
            self.redo_lock.release()
            yield redo