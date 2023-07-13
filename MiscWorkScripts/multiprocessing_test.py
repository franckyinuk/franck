import multiprocessing
import time
import os

"""Here is the command to make it an executable cxfreeze multiprocessing_test.py --target-dir multiprocessing"""

def thread_task(dummy):
    time.sleep(3)

def main():
    print("This program has 8 tasks of 3 seconds to execute")
    pool = multiprocessing.Pool()		# starts has many worker as processes

    pool.map(thread_task, [""] * 8)		# call thread_task 8 times
    
    

if __name__ == '__main__':
    multiprocessing.freeze_support()		# this line is necessary to turn the code into an executable
    start = time.time()
    main()
    end = time.time()
    print("Completed in %f seconds" % (end-start))
    
