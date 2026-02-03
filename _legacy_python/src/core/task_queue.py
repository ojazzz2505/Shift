import concurrent.futures
import time
from ..utils.logger import logger

class TaskQueue:
    def __init__(self, max_workers=4):
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self.futures = {} # task_id -> future
        self.callbacks = {} # task_id -> callback
        self.running = True

    def submit_task(self, task_id, func, *args, callback=None, **kwargs):
        """
        Submits a task to the thread pool.
        func: The function to execute.
        callback: Function to call with result/progress.
        """
        if not self.running:
            logger.warning("TaskQueue is shutting down, cannot submit task.")
            return

        future = self.executor.submit(func, *args, **kwargs)
        self.futures[task_id] = future
        if callback:
            self.callbacks[task_id] = callback
            future.add_done_callback(lambda f: self._on_task_done(task_id, f))
            
        logger.info(f"Task {task_id} submitted.")
        return future

    def cancel_task(self, task_id):
        if task_id in self.futures:
            future = self.futures[task_id]
            # Cancel only works if task hasn't started, unless logic inside checks for cancellation
            cancelled = future.cancel()
            logger.info(f"Task {task_id} cancellation requested. Cancelled: {cancelled}")
            # Identify if running and signal it (needs engine support)
            return cancelled
        return False

    def _on_task_done(self, task_id, future):
        try:
            result = future.result()
            # If callback exists, call it
            if task_id in self.callbacks:
                # We might want to dispatch this to the main thread in a real UI app
                # But customtkinter is usually thread-safe for basic updates or needs .after
                pass 
        except concurrent.futures.CancelledError:
            logger.info(f"Task {task_id} was cancelled.")
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            
        # Cleanup
        self.futures.pop(task_id, None)
        self.callbacks.pop(task_id, None)

    def shutdown(self):
        self.running = False
        self.executor.shutdown(wait=False)
