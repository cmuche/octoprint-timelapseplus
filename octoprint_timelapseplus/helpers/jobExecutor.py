import concurrent


class JobExecutor:

    def __init__(self, jobs, callbackExecute, callbackProgress):
        self.JOBS = jobs
        self.COUNT_JOBS = len(jobs)

        self.CALLBACK_EXECUTE = callbackExecute
        self.CALLBACK_PROGRESS = callbackProgress

        self.LAST_PROGRESS = 0

    def start(self):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(self.processJob, job) for job in self.JOBS]
            concurrent.futures.wait(futures)

    def increaseProgress(self):
        self.LAST_PROGRESS = self.LAST_PROGRESS + 1
        self.CALLBACK_PROGRESS(self.LAST_PROGRESS / self.COUNT_JOBS)

    def processJob(self, job):
        self.CALLBACK_EXECUTE(job)
        self.increaseProgress()
