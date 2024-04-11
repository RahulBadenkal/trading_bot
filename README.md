- By default, a python program when run, utilizes only 1 core
- If multiple threads are spawned, then at any point only 1 thread will be executing but the order is managed by the os.
  Ex: If you run 2 threads each printing numbers from 1-10,000. Then thread 1 might print from 1-20, then the os might pause thread1 and execute thread2 (print 1-10), then resume thread1 again. So unlike nodejs we might have race conditions
- We need to use multiprocessing module in python to utilize all cores. Multiprocessing just spins new python process (new python interpreter) in the background to achieve it.
  But multiprocess doesn't benefit when there is only 1 core


Reference links
- https://stackoverflow.com/a/63519065/4947985
- https://www.quora.com/Does-Erlang-use-all-the-existing-cores-automatically
- https://github.com/tiangolo/fastapi/issues/520#issuecomment-667428023
- https://www.google.com/url?sa=t&source=web&rct=j&opi=89978449&url=https://anecdotes.dev/fastapi-scale-with-non-asyncio-requests-handling-e10b181eaa02%23:~:text%3DWhen%2520FastAPI%2520is%2520used%2520asynchronously,allowing%2520context%2520switches%2520between%2520them.%26text%3DThis%2520way%252C%2520FastAPI%2520appears%2520to,this%2520is%2520not%2520entirely%2520accurate.&ved=2ahUKEwjwqKbDz7mFAxWW6jgGHSoHBfoQFnoECBIQBQ&usg=AOvVaw1F_J3lnLxWNlBP9F-jZms5
- 