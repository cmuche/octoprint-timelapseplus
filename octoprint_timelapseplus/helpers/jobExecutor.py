import concurrent
import os


class JobExecutor:

    def __init__(self, settings, jobs, callbackExecute, callbackProgress):
        self._settings = settings
        self.JOBS = jobs
        self.COUNT_JOBS = len(jobs)

        self.CALLBACK_EXECUTE = callbackExecute
        self.CALLBACK_PROGRESS = callbackProgress

        self.LAST_PROGRESS = 0

        self.CPU_COUNT = os.cpu_count()

    def start(self):
        numWorkers = 1
        if self._settings.get(["renderMultithreading"]):
            numWorkers = max(1, int(self.CPU_COUNT / 2))

        with concurrent.futures.ThreadPoolExecutor(max_workers=numWorkers) as executor:
            futures = [executor.submit(self.processJob, job) for job in self.JOBS]
            concurrent.futures.wait(futures)

    def increaseProgress(self):
        self.LAST_PROGRESS = self.LAST_PROGRESS + 1
        self.CALLBACK_PROGRESS(self.LAST_PROGRESS / self.COUNT_JOBS)

    def processJob(self, job):
        self.CALLBACK_EXECUTE(job)
        self.increaseProgress()
