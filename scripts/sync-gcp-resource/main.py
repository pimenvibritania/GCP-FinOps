import concurrent.futures
import subprocess
import logging
import sys
from datetime import datetime, timedelta

# Configure separate loggers for info and errors
info_logger = logging.getLogger('info_logger')
info_logger.setLevel(logging.INFO)
info_handler = logging.FileHandler('info_log.log')
info_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
info_logger.addHandler(info_handler)

error_logger = logging.getLogger('error_logger')
error_logger.setLevel(logging.ERROR)
error_handler = logging.FileHandler('error_log.log')
error_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
error_logger.addHandler(error_handler)


def run_task(command):
    """Run a shell command and return its output."""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        info_logger.info(f"Task {command} completed successfully:\n{result.stdout}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        error_logger.error(f"Error executing {command}: {e}\n{e.stderr}")
        return f"Error executing {command}: {e}"


def main(date_start, c_day, c_loop):
    # List of commands/scripts to run
    tasks = []
    add_day = 0

    for loop in range(c_loop):
        date_start_use = date_start + timedelta(days=add_day)
        date_start_use_str = date_start_use.strftime("%Y-%m-%d")

        command = f"python3 ../../manage.py sync_gcp_cost_resource {date_start_use_str} {c_day}"
        tasks.append(command)
        add_day += int(c_day)

    # Create a ThreadPoolExecutor to run tasks concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        # Submit tasks to the executor
        future_to_task = {executor.submit(run_task, task): task for task in tasks}

        # Process results as they complete
        for future in concurrent.futures.as_completed(future_to_task):
            task = future_to_task[future]
            print(task)
            try:
                result = future.result()
                print(result)
            except Exception as e:
                error_logger.error(f"Task {task} generated an exception: {e}")
            else:
                info_logger.info(f"Task {task} result:\n{result}")


if __name__ == "__main__":
    start_date = datetime.strptime(sys.argv[1], "%Y-%m-%d")
    days = sys.argv[2]
    total_loop = int(sys.argv[3])
    main(start_date, days, total_loop)
