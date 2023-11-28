import shutil
import sys
import subprocess
import os
from pathlib import Path


def check_call(args, cwd):
    """
    Executes a command with arguments in a specified directory and checks the return code.

    Args:
        args (list): A list of command-line arguments to execute.
        cwd (str): The directory to execute the command in.

    Returns:
        bytes: The standard output of the executed command.

    Raises:
        subprocess.CalledProcessError: If the command returns a non-zero exit code.
    """
    proc = subprocess.Popen(args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd)
    stdout, stderr = proc.communicate()
    if proc.returncode != 0:
        print(stderr)
        raise subprocess.CalledProcessError(
            returncode=proc.returncode,
            cmd=args)
    
    return stdout


print("Preparing package...")
resourcedir = Path("resources") / sys.argv[1].split("::")[1].lower() / sys.argv[1].replace("::","-")

print("Submitting...")
check_call(['cfn', 'submit', '--set-default'], resourcedir.absolute())

print("Cleaning up...")
shutil.rmtree((resourcedir / "build").absolute())
