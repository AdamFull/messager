from shutil import rmtree
from os import remove

if __name__ == "__main__":
    paths = ['Server/Log/', 'Server/Data/', 'Server/__pycache__/', 'Client/config/', 'Client/Log/', 'Client/__pycache__/', '__pycache__/', '.vscode/']
    for path in paths:
        rmtree(path, ignore_errors=True)

