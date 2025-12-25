"""
Download Manager with Queue System
Handles sequential download processing with retry capabilities.
"""

import os
import threading
from typing import Optional, Callable, List
from dataclasses import dataclass, field
from enum import Enum
import time
from queue import Queue
from chorus_api import Chart, ChorusAPI


class DownloadStatus(Enum):
    """Download status states."""
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass
class DownloadTask:
    """Represents a download task."""
    chart: Chart
    output_path: str
    include_video: bool = True
    status: DownloadStatus = DownloadStatus.QUEUED
    progress: float = 0.0
    error_message: str = ""
    retry_count: int = 0
    max_retries: int = 3

    def get_filename(self) -> str:
        """Get the output filename."""
        return os.path.basename(self.output_path)


class DownloadManager:
    """
    Manages sequential chart downloads with queue system.

    Features:
    - Sequential processing (one download at a time)
    - Automatic retries on failure
    - Progress tracking
    - Cancellation support
    - Callback notifications
    """

    def __init__(self, clone_hero_path: Optional[str] = None):
        """
        Initialize the download manager.

        Args:
            clone_hero_path: Path to Clone Hero Songs directory
        """
        self.clone_hero_path = clone_hero_path or self._get_default_ch_path()
        self.api = ChorusAPI()

        # Download queues
        self.download_queue: List[DownloadTask] = []
        self.retry_queue: List[DownloadTask] = []
        self.completed: List[DownloadTask] = []
        self.errored: List[DownloadTask] = []

        # Threading
        self.worker_thread: Optional[threading.Thread] = None
        self.is_running = False
        self.lock = threading.Lock()

        # Callbacks
        self.progress_callback: Optional[Callable[[DownloadTask], None]] = None
        self.completion_callback: Optional[Callable[[DownloadTask], None]] = None
        self.error_callback: Optional[Callable[[DownloadTask, str], None]] = None

    def _get_default_ch_path(self) -> str:
        """Get default Clone Hero Songs path."""
        if os.name == 'nt':  # Windows
            return r"C:\Program Files\Clone Hero\Songs"
        else:
            return os.path.expanduser("~/Clone Hero/Songs")

    def set_clone_hero_path(self, path: str):
        """Set the Clone Hero Songs directory path."""
        if os.path.isdir(path):
            self.clone_hero_path = path
        else:
            raise ValueError(f"Invalid path: {path}")

    def add_download(
        self,
        chart: Chart,
        include_video: bool = True,
        custom_folder_name: Optional[str] = None
    ) -> DownloadTask:
        """
        Add a chart to the download queue.

        Args:
            chart: Chart to download
            include_video: Whether to include video background
            custom_folder_name: Custom folder name (default: artist - song name)

        Returns:
            The created DownloadTask
        """
        # Generate folder name
        if custom_folder_name:
            folder_name = custom_folder_name
        else:
            folder_name = f"{chart.artist} - {chart.name}"
            # Clean folder name
            folder_name = self._sanitize_filename(folder_name)

        # Create output directory
        chart_dir = os.path.join(self.clone_hero_path, folder_name)
        os.makedirs(chart_dir, exist_ok=True)

        # Output file path
        output_path = os.path.join(chart_dir, f"{chart.md5}.sng")

        # Check for duplicates
        with self.lock:
            for task in self.download_queue + self.retry_queue:
                if task.chart.md5 == chart.md5:
                    print(f"Chart already in queue: {chart.name}")
                    return task

        # Create download task
        task = DownloadTask(
            chart=chart,
            output_path=output_path,
            include_video=include_video
        )

        with self.lock:
            self.download_queue.append(task)

        # Start worker if not running
        if not self.is_running:
            self.start()

        return task

    def add_multiple(
        self,
        charts: List[Chart],
        include_video: bool = True
    ) -> List[DownloadTask]:
        """
        Add multiple charts to download queue.

        Args:
            charts: List of charts to download
            include_video: Whether to include video backgrounds

        Returns:
            List of created DownloadTasks
        """
        tasks = []
        for chart in charts:
            task = self.add_download(chart, include_video)
            tasks.append(task)
        return tasks

    def cancel_download(self, task: DownloadTask):
        """Cancel a queued or active download."""
        with self.lock:
            task.status = DownloadStatus.CANCELLED

            # Remove from queue
            if task in self.download_queue:
                self.download_queue.remove(task)
            if task in self.retry_queue:
                self.retry_queue.remove(task)

    def retry_failed(self, task: DownloadTask):
        """Retry a failed download."""
        with self.lock:
            if task in self.errored:
                self.errored.remove(task)

            task.status = DownloadStatus.QUEUED
            task.retry_count = 0
            task.error_message = ""
            task.progress = 0.0

            self.retry_queue.append(task)

        # Start worker if not running
        if not self.is_running:
            self.start()

    def start(self):
        """Start the download worker thread."""
        if not self.is_running:
            self.is_running = True
            self.worker_thread = threading.Thread(target=self._worker, daemon=True)
            self.worker_thread.start()

    def stop(self):
        """Stop the download worker thread."""
        self.is_running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)

    def _worker(self):
        """Worker thread for processing downloads."""
        while self.is_running:
            # Get next task
            task = self._get_next_task()

            if not task:
                # No tasks, sleep and check again
                time.sleep(0.5)
                continue

            # Process download
            self._process_download(task)

        print("Download worker stopped")

    def _get_next_task(self) -> Optional[DownloadTask]:
        """Get the next task to process."""
        with self.lock:
            # Prioritize retry queue
            if self.retry_queue:
                task = self.retry_queue.pop(0)
                return task

            # Then main queue
            if self.download_queue:
                task = self.download_queue.pop(0)
                return task

            # No tasks, stop worker
            if not self.download_queue and not self.retry_queue:
                self.is_running = False

        return None

    def _process_download(self, task: DownloadTask):
        """Process a single download task."""
        if task.status == DownloadStatus.CANCELLED:
            return

        # Update status
        with self.lock:
            task.status = DownloadStatus.DOWNLOADING
            task.progress = 0.0

        print(f"Downloading: {task.chart.name} by {task.chart.artist}")

        # Progress callback
        def on_progress(percent: float):
            with self.lock:
                task.progress = percent
            if self.progress_callback:
                self.progress_callback(task)

        # Download
        try:
            success = self.api.download_chart(
                task.chart,
                task.output_path,
                task.include_video,
                on_progress
            )

            if success and task.status != DownloadStatus.CANCELLED:
                # Download complete
                with self.lock:
                    task.status = DownloadStatus.COMPLETED
                    task.progress = 100.0
                    self.completed.append(task)

                print(f"✓ Downloaded: {task.chart.name}")

                if self.completion_callback:
                    self.completion_callback(task)

            elif not success:
                # Download failed
                self._handle_error(task, "Download failed")

        except Exception as e:
            # Error occurred
            self._handle_error(task, str(e))

    def _handle_error(self, task: DownloadTask, error: str):
        """Handle download error with retry logic."""
        task.retry_count += 1

        if task.retry_count < task.max_retries:
            # Retry
            print(f"⚠ Download error (retry {task.retry_count}/{task.max_retries}): {task.chart.name}")
            with self.lock:
                task.status = DownloadStatus.QUEUED
                task.error_message = error
                self.retry_queue.append(task)

        else:
            # Max retries reached
            print(f"✗ Download failed: {task.chart.name} - {error}")
            with self.lock:
                task.status = DownloadStatus.ERROR
                task.error_message = error
                self.errored.append(task)

            if self.error_callback:
                self.error_callback(task, error)

    def _sanitize_filename(self, filename: str) -> str:
        """Remove invalid characters from filename."""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename.strip()

    def get_queue_status(self) -> dict:
        """Get current queue status."""
        with self.lock:
            return {
                "queued": len(self.download_queue),
                "retry": len(self.retry_queue),
                "completed": len(self.completed),
                "errored": len(self.errored),
                "is_running": self.is_running
            }

    def get_all_tasks(self) -> dict:
        """Get all tasks organized by status."""
        with self.lock:
            return {
                "queue": list(self.download_queue),
                "retry": list(self.retry_queue),
                "completed": list(self.completed),
                "errored": list(self.errored)
            }

    def clear_completed(self):
        """Clear completed downloads from list."""
        with self.lock:
            self.completed.clear()


if __name__ == "__main__":
    # Test download manager
    from chorus_api import SearchParams

    print("Download Manager Test")
    print("=" * 60)

    # Search for charts
    api = ChorusAPI()
    params = SearchParams(query="test", per_page=3)
    result = api.search(params)

    if not result.charts:
        print("No charts found for testing")
        exit()

    # Create download manager
    manager = DownloadManager()

    # Set up callbacks
    def on_progress(task: DownloadTask):
        print(f"  Progress: {task.progress:.1f}% - {task.chart.name}")

    def on_complete(task: DownloadTask):
        print(f"  ✓ Complete: {task.chart.name}")

    def on_error(task: DownloadTask, error: str):
        print(f"  ✗ Error: {task.chart.name} - {error}")

    manager.progress_callback = on_progress
    manager.completion_callback = on_complete
    manager.error_callback = on_error

    # Add downloads
    print(f"\nAdding {len(result.charts)} charts to queue...")
    tasks = manager.add_multiple(result.charts[:2], include_video=False)

    # Wait for completion
    print("\nDownloading...")
    while manager.is_running:
        time.sleep(1)
        status = manager.get_queue_status()
        print(f"Status: {status}")

    print("\nDownload test complete!")
    final_status = manager.get_queue_status()
    print(f"Final status: {final_status}")
