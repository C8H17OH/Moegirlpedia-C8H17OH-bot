import pywikibot
import queue
import threading
import time
from disambig_linkshere import disambig_linkshere_action


class Task():
    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs
    
    def call(self):
        return self.func(*self.args, **self.kwargs)


def process_print(*args, **kwargs):
    # print("process", *args, **kwargs)
    pass


class TaskProcess(threading.Thread):
    def __init__(self):
        process_print("init")
        threading.Thread.__init__(self)
        self.tasks = queue.Queue()
        self.task_lock = threading.Lock()
        self.running = True
        self.over = False
        self.redos = queue.Queue()
        self.redo_lock = threading.Lock()

    def add(self, task):
        self.task_lock.acquire()
        self.tasks.put(task)
        self.task_lock.release()

    def print(self, *args, **kwargs):
        process_print("print:", args, kwargs)
        self.add(Task(print, *args, **kwargs))

    def action(self, *args, **kwargs):
        process_print("action:", args, kwargs)
        self.add(Task(disambig_linkshere_action, *args, **kwargs))

    def run(self):
        process_print("before running")
        while self.running and not self.over:
            process_print("running")
            self.task_lock.acquire()
            if not self.tasks.empty():
                task = self.tasks.get()
                self.task_lock.release()
                ret = task.call()
                if ret == "redo":
                    self.redo_lock.acquire()
                    self.redos.put(task.kwargs["disambig"] if task.kwargs.get("disambig") else task.args[0])
                    self.redo_lock.release()
                elif ret == "quit":
                    self.running = False
                    self.wait()
                    exit(0)
            else:
                self.task_lock.release()
                time.sleep(1)

    def wait(self):
        self.over = True
        self.join()
    
    def no_redo(self):
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