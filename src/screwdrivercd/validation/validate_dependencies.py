# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
"""
Dependency security validation wrapper for screwdrivercd

This wrapper runs the validation tool.  This wrapper does the following:

- Runs the dependency checking tool
- ensures all the logs and reports are stored in the build artifacts before exiting.
"""
from ..screwdriver.environment import logging_basicConfig, update_job_status
logging_basicConfig(check_prefix='DEPENDENCY_CHECK')

import json
import logging
import os
import sys

from termcolor import colored
from pypirun.cli import install_and_run, interpreter_parent
from ..utility import create_artifact_directory, env_bool
from ..utility.package import PackageMetadata


logger_name = 'validate_dependencies' if __name__ == '__main__' else __name__
logger = logging.getLogger(logger_name)


def validate_with_safety():
    """Run the safety command in a virtualenv to validate the package dependencies"""

    artifacts_dir = os.environ.get('SD_ARTIFACTS_DIR', '')
    report_dir = os.path.join(artifacts_dir, 'reports/dependency_validation')
    create_artifact_directory(report_dir)
    
    interpreter = interpreter_parent(sys.executable)
    interpreter = os.environ.get('BASE_PYTHON', interpreter)

    # Generate a full text report
    full_report_filename = os.path.join(report_dir, 'safetydb.full')
    rc = install_and_run(package='safety,.', command=f'safety check --full-report -o "{full_report_filename}"', interpreter=interpreter, upgrade_setuptools=True, upgrade_pip=True)

    if rc == 0:
        update_job_status(status='SUCCESS', message='Dependency check passed')
        print(colored('Safetydb check passed', color='green'))
        return rc

    # Generate the report in json format
    json_report_filename = os.path.join(report_dir, 'safetydb.json')
    rc = install_and_run(package='safety,.', command=f'safety check --json -o "{json_report_filename}"', interpreter=interpreter, upgrade_setuptools=True, upgrade_pip=True)

    bad_packages = -1
    if os.path.exists(json_report_filename):
        with open(json_report_filename) as fh:
            results = json.load(fh)
            bad_packages = len(results)

    update_job_status(status='FAILURE', message=f'Dependency check failed {bad_packages} bad dependencies found')

    return rc


def main():
    """
    Type check runner utility command line entry point

    Returns
    -------
    int:
        Returncode from running the check
    """
    return validate_with_safety()
