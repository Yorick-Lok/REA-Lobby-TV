import subprocess
import threading
from pathlib import Path
import random

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main import Server

class Transcoding:
    def __init__( self, context : "Server" ) -> None:
        self.transcoding            = False
        self.transcoding_file       = False
        self.transcoding_progress   = False
        self.transcoding_process    = None

        self.transcoding_cancel = threading.Event()
        self.transcoding_thread = None

        self.context : Server       = context

    def get_status(self) -> dict:
        return {
            "transcoding" : {
                "state"     : self.transcoding,
                "file"      : self.transcoding_file,
                "progress"  : self.transcoding_progress
            }
        }

    def get_video_duration(self, file: Path) -> float:
        """Get video duration in seconds using ffprobe."""
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(file)
            ],
            capture_output=True,
            text=True,
            check=True
        )
        return float(result.stdout.strip())

    def cancel_transcoding(self) -> None:
        process = self.transcoding_process
        thread = self.transcoding_thread

        if process is None and thread is None:
            print("[Transcoding] Nothing to cancel")
            return

        print(f"[Transcoding] Cancelling PID {process.pid if process else None}")

        self.transcoding_cancel.set()

        if process and process.poll() is None:
            print("[Transcoding] Sending terminate...")
            process.terminate()

            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print("[Transcoding] Terminate timed out, killing process...")
                process.kill()
                process.wait()

        if process:
            print(f"[Transcoding] Process exited: {process.poll()}")

        if thread and thread.is_alive():
            print("[Transcoding] Waiting for monitoring thread...")
            thread.join()

        print("[Transcoding] Monitoring thread finished")

        self.transcoding_process    = None
        self.transcoding_thread     = None
        self.transcoding            = False
        self.transcoding_file       = False
        self.transcoding_progress   = False
        self.context.socketio.emit("status", self.get_status())

        print("[Transcoding] Cancellation complete")
        
    def start_transcoding(self) -> None:
        """Start FFmpeg in a separate process."""
        # Cancel previous transcoding if still running
        self.cancel_transcoding()
        self.transcoding_cancel.clear()

        static_dir = Path(__file__).resolve().parent / "static"
        input_file = static_dir / "Screen.mp4"
        output_file = static_dir / "Screen-transcoding.mp4"
        backup_file = static_dir / "Screen-unencoded.mp4"

        try:
            duration = self.get_video_duration(input_file)
        except (OSError, subprocess.SubprocessError, ValueError) as e:
            return {
                "success"   : False,
                "message"   : f"Could not determine video duration: {e}"
            }

        command = [
            "ffmpeg",
            "-hide_banner",
            "-y",
            "-fflags", "+discardcorrupt",
            "-err_detect", "ignore_err",
            "-i", str(input_file),
            "-map", "0:v:0",
            "-map", "0:a?",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "20",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            "-progress", "pipe:1",
            "-nostats",
            str(output_file)
        ]

        try:
            self.transcoding_process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                bufsize=1
            )
        except OSError as e:
            return {
                "success"   : False,
                "message"   : f"Failed to start FFmpeg: {e}"
            }

        self.transcoding = True
        self.transcoding_file = "Screen.mp4"
        self.transcoding_progress = 0 if duration else False
        self.context.socketio.emit("status", self.get_status())

        self.transcoding_thread = threading.Thread(
            target=self.monitor_transcoding,
            args=(self.transcoding_process, duration, input_file, output_file, backup_file),
            daemon=True
        )
        self.transcoding_thread.start()

        return {
            "success"   : True,
            "message"   : "Transcoding started"
        }

    def transcoding_complete_success(self, input_file: Path, output_file: Path, backup_file: Path) -> None:
        # Remove previous backup (Screen-unencoded.mp4), if it exists
        # And preserve the original uploaded video 
        # (Screen.mp4 -. Screen-unencoded.mp4)
        backup_file.unlink(missing_ok=True)
        input_file.rename(backup_file)

        # Replace the original video with the transcoded version 
        # (Screen-transcoding.mp4 -> Screen.mp4)
        output_file.rename(input_file)

    def monitor_transcoding(self, process: subprocess.Popen, duration: float | None, input_file: Path, output_file: Path, backup_file: Path) -> None:
        """Monitor FFmpeg progress and update application state."""
        last_progress = -1

        for line in process.stdout:
            key, _, value = line.strip().partition("=")

            if key == "out_time_us" and duration:
                try:
                    current_time = int(value) / 1_000_000
                    progress = min(99, int(current_time / duration * 100))

                    if progress != last_progress:
                        last_progress = progress
                        self.transcoding_progress = progress
                        self.context.socketio.emit("status", self.get_status())

                except ValueError:
                    pass

            elif key == "progress" and value == "end":
                self.transcoding_progress = 100
                self.context.socketio.emit("status", self.get_status())

        return_code = process.wait()

        if process.stdout:
            process.stdout.close()

        if self.transcoding_cancel.is_set():
            print("Transcoding cancelled")

        elif return_code == 0:
            print("Transcoding completed successfully")
            self.transcoding_complete_success(input_file, output_file, backup_file)

            # update the active browser forcing a video reload
            data = {
                "number": random.randrange(20, 5000, 3)
            }
            self.context.socketio.emit("state", data)

        else:
            print(f"Transcoding failed with exit code {return_code}")

        self.transcoding            = False
        self.transcoding_file       = False
        self.transcoding_progress   = False
        self.transcoding_process    = None
        self.context.socketio.emit("status", self.get_status())