import time
from pipeline import run_full_pipeline

INTERVAL_SECONDS = 60 * 60 * 3  # 3 hours


def main():
    while True:
        try:
            print("Running pipeline...")
            run_full_pipeline()
            print("Pipeline completed successfully.")
        except Exception as e:
            print(f"Pipeline error: {e}")

        print("Sleeping for 3 hours...")
        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
