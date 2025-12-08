"""
Scheduler Runner - APScheduler Configuration
"""
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger
import pytz

from app.config import settings
from app.scheduler.jobs import sync_run_daily_job


class SchedulerRunner:
    """APScheduler runner for background jobs."""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler(
            timezone=pytz.timezone(settings.SCHEDULER_TIMEZONE)
        )
        self._setup_jobs()
    
    def _setup_jobs(self):
        """Configure scheduled jobs."""
        # Daily crystal job at 06:00
        self.scheduler.add_job(
            sync_run_daily_job,
            CronTrigger(
                hour=settings.DAILY_JOB_HOUR,
                minute=settings.DAILY_JOB_MINUTE,
                timezone=pytz.timezone(settings.SCHEDULER_TIMEZONE)
            ),
            id="daily_crystal_job",
            name="Daily Crystal Sentiment Collection",
            replace_existing=True,
        )
        
        logger.info(
            f"Scheduled daily job at {settings.DAILY_JOB_HOUR:02d}:{settings.DAILY_JOB_MINUTE:02d} "
            f"({settings.SCHEDULER_TIMEZONE})"
        )
    
    def start(self):
        """Start the scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")
    
    def stop(self):
        """Stop the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")
    
    def get_jobs(self):
        """Get list of scheduled jobs."""
        jobs = []
        for job in self.scheduler.get_jobs():
            next_run = job.next_run_time
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": next_run.isoformat() if next_run else None,
            })
        return jobs
    
    def run_job_now(self, job_id: str = "daily_crystal_job"):
        """Trigger a job immediately."""
        job = self.scheduler.get_job(job_id)
        if job:
            job.modify(next_run_time=datetime.now(pytz.timezone(settings.SCHEDULER_TIMEZONE)))
            logger.info(f"Triggered job: {job_id}")
            return True
        return False


# Global scheduler instance
scheduler_runner = SchedulerRunner()
