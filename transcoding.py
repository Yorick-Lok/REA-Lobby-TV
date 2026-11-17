import subprocess
import threading
from pathlib import Path
import shutil

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

        _static_dir = Path(__file__).resolve().parent / "static"
        self.input_file     = _static_dir / "Screen.mp4"
        self.output_file    = _static_dir / "Screen-transcoding.mp4"
        self.backup_file    = _static_dir / "Screen-unencoded.mp4"
        
        self.context : Server       = context

    def has_temp_trancodeded_video(self):
        return self.output_file.exists() and not self.transcoding

    def get_status(self) -> dict:
        return {
            "transcoding" : {
                "state"             : self.transcoding,
                "file"              : self.transcoding_file,
                "progress"          : self.transcoding_progress,
                "use_transcoded"    : not self.has_temp_trancodeded_video()
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

        try:
            duration = self.get_video_duration(self.input_file)
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
            args=(self.transcoding_process, duration),
            daemon=True
        )
        self.transcoding_thread.start()

        return {
            "success"   : True,
            "message"   : "Transcoding started"
        }

    def replace_files_post_transcoding(self) -> None:
        try:
            # make sure there are no active file locks
            self.context.stop_client_playback()

            # Replace previous backup (Screen-unencoded.mp4)
            self.backup_file.unlink(missing_ok=True)
            shutil.copy2(self.input_file, self.backup_file)

            # Replace the original video with the transcoded version 
            # (Screen-transcoding.mp4 -> Screen.mp4)
            self.output_file.replace(self.input_file)

            # refresh any active client browsers forcing a video reload
            self.context.refresh_client()

        except Exception as e:
            print(f"[Transcoding] Failed to replace original video: {e}")
            raise

    def monitor_transcoding(self, process: subprocess.Popen, duration: float | None) -> None:
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

        try:
            if self.transcoding_cancel.is_set():
                print("Transcoding cancelled")
            elif return_code == 0:
                print("Transcoding completed successfully")
                self.replace_files_post_transcoding()
            else:
                print(f"Transcoding failed with exit code {return_code}")

        finally:
            self.transcoding            = False
            self.transcoding_file       = False
            self.transcoding_progress   = False
            self.transcoding_process    = None
            self.context.socketio.emit("status", self.get_status())
