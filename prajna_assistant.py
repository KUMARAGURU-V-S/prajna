import sys
import os

# Add local path if needed
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import sentry

if __name__ == "__main__":
    print("Initializing Prajna Voice Assistant...")
    try:
        sentry.listen()
    except KeyboardInterrupt:
        print("\nPrajna shut down gracefully.")