"""
DigitalOcean Worker Entrypoint
Runs every 3 hours
"""

import time
from pipeline import TravelAdvisoryPipeline

INTERVAL_SECONDS = 60 * 60 * 3  # 3 hours


def main():
    pipeline = TravelAdvisoryPipeline()

    while True:
        try:
            pipeline.run()
        except Exception as e:
            print(f"Pipeline crashed: {e}")

        print("Sleeping 3 hours...")
        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
