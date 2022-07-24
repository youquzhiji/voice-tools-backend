from subprocess import check_output

try:
    COMMIT_NUM = " alpha " + check_output(['git', 'rev-list', '--count', 'main']).decode().strip()
except Exception as e:
    COMMIT_NUM = ""

VERSION = "2.0.0" + COMMIT_NUM
VERSION_SHORT = VERSION.replace(' alpha ', 'a')
