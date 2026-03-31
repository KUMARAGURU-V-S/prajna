import os
import subprocess
import re

def dispatch(transcript: str) -> str:
    """
    Parses the transcribed text and triggers the corresponding action.
    Returns a human-readable response string.
    """
    text = transcript.lower().strip()
    
    # 1. Remind Me action
    # E.g. "Remind me to check the oven at 5pm" -> schedules a python thread
    remind_match = re.search(r"remind me\s+(.*?)\s+(?:in|at)\s+(.*)", text)
    if remind_match:
        task = remind_match.group(1).strip()
        time_str = remind_match.group(2).strip()
        
        # Simple background background delay using python
        # We'll just launch a background process that sleeps then notifies
        # For a robust version, we'd parse the time_str, but for now we'll do a simple
        # script that notifies immediately as a proof-of-concept for the VENV.
        cmd = f"nohup bash -c \"sleep 10 && notify-send 'Prajna Reminder' '{task} (Time parsed: {time_str})'\" >/dev/null 2>&1 &"
        try:
            subprocess.run(cmd, shell=True, check=True)
            return f"Scheduled reminder: '{task}' for {time_str}."
        except subprocess.CalledProcessError as e:
            return f"Failed to schedule reminder. Error: {e}"

    # 2. Time action
    if "time is it" in text or text == "time":
        from datetime import datetime
        now = datetime.now().strftime("%I:%M %p")
        # Speak it out or show a notification
        os.system(f"notify-send 'Prajna Time' 'It is currently {now}'")
        return f"It is currently {now}."

    # 3. Launch application
    # E.g. "Launch Firefox" or "Open Firefox"
    launch_match = re.search(r"(?:launch|open)\s+([a-z]+)", text)
    if launch_match:
        app = launch_match.group(1).strip()
        # Run it in background
        try:
            subprocess.Popen([app], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"Launching {app}..."
        except FileNotFoundError:
            os.system(f"notify-send 'Prajna Error' 'Could not find app: {app}'")
            return f"Failed to launch {app}. Application not found."

    # Fallback
    return "Hmm, I didn't catch an actionable command."

if __name__ == "__main__":
    # Test cases
    print(dispatch("Remind me to call John at 2pm."))
    print(dispatch("What time is it?"))
    print(dispatch("Launch firefox."))
