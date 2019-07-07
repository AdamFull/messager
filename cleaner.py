from shutil import rmtree

if __name__ == "__main__":
    paths = ['Server/Log/', 'Server/Data/', 'Server/__pycache__/', 'Client/config/', 'Client/Log/', 'Client/__pycache__/']
    for path in paths:
        rmtree(path, ignore_errors=True)

