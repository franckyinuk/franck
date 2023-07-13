import multiprocessing
import time
import subprocess

mutex = multiprocessing.Lock()
size_of_test_groups = 75 # with 100 it fails because the command size exceed the maximum size of 8191

def safe_print(text):
    global mutex
    mutex.acquire()
    print(text)
    mutex.release()

def split_list(a_list, chunk_size):
    """ produces a generator, can be converted to a list: list(split_list(list(range(100)), 10))
    	Yield successive n-sized chunks from l.
    """
    for i in range(0, len(a_list), chunk_size):
        yield a_list[i:i+chunk_size]

def collect_test_names():
    p = subprocess.Popen(["ConApp.exe", "--PrintTestNames"], stdout = subprocess.PIPE, universal_newlines = True)
    names = p.communicate()[0].split("\n")
    return names
    
def conapp_task(tests):
    command = ["ConApp.exe", "-alltests",  "-nowait",  "-exactname"] + list(tests)
    p = subprocess.Popen(command, stdout = subprocess.PIPE, universal_newlines = True, shell = True)
    result = p.communicate()[0]

    # only print the output if the tests failed
    if not result.endswith("PPPP\n"):
        safe_print(' '.join(command))
        safe_print(result)
    
def main():
    start = time.time()

    # create a pool of workers, starts with has many worker as cores
    pool = multiprocessing.Pool()

    # collect all the test names to run
    tests = collect_test_names()

    # split the tests into groups
    splitted_tests = []
    if (size_of_test_groups < len(tests)):
        splitted_tests = split_list(tests, size_of_test_groups)
    else:
        splitted_tests = [tests]
        
    # assign the work to the workers
    pool.map(conapp_task, splitted_tests)

    end = time.time()
    print("Completed in %f seconds" % (end-start))
    
if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()
    
