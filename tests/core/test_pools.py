# Module:   test_pools
# Date:     22nd February 2011
# Author:   James Mills, prologic at shortcircuit dot net dot au

"""Pools Tests"""

from time import sleep

import pytest

from circuits import Task, Pool

def f():
    x = 0
    i = 0
    while i < 1000000:
        x += 1
        i += 1
    return x

def test():
    p = Pool()
    p.start()

    x = p.push(Task(f))

    sleep(1)

    result = pytest.wait_for(x, "result")
    assert result

    result = x.result
    assert result

    value = x.value
    assert value == 1000000

    p.stop()
