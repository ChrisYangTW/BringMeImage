import re
import subprocess


def get_pid(process_name: str) -> list:
    pid: list = []
    paser = re.compile(r'^\S*\s+(\d+)\s+')

    if process_name == 'GoogleChrome':
        command = "ps aux | grep '[M]acOS/Google Chrome [^H]'"
    elif process_name == 'chromedriver':
        command = "ps aux | grep '[c]hromedriver.*chromedriver'"
    else:
        raise AssertionError('process_name must be either GoogleChrome or chromedriver')

    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.stdout:
        for result in result.stdout.splitlines():
            match = paser.match(result)
            if match:
                pid.append(match.group(1))

    return pid


def clear_chromedriver_process(chromedriver_pid: list, google_chrome_pid: list) -> None:
    for chromedriver_pid in chromedriver_pid:
        subprocess.run(f'kill -TERM {chromedriver_pid}', shell=True)
    for google_chrome_pid in google_chrome_pid:
        subprocess.run(f'kill -TERM {google_chrome_pid}', shell=True)