---
id: '53e13aa4-b691-47df-a28d-a598ebd662f4'
date: '2017-04-08T12:23:33-05:00'
title: "Implementing a JavaScript like Promise system in C++"
tags: [C++, Multithreading, Async]
categories: [technical]
type: 'blog'
draft: true
---

In the process of learn some of the new features that the C++14 and C++17
standard has, and as part of the work I've been doing on certain library that
requires some asynchronus HTTP calls, I had the idea of creating a library that
handles Promises on C++.

When I started learning JavaScript and got into Promises I got really fascinated
of this system that handles asyncronus calls so easily and provides the expected
value when it's available. I really wanted this on C++.

## JavaScript Promises

The workflow that JavaScript uses for it's promises is preatty straight forward:

![JavaScript Promises Workflow](https://media.prod.mdn.mozit.cloud/attachments/2018/04/18/15911/32e79f722e83940fdaea297acdb5df92/promises.png)

> Extracted from https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise

When creating one it requires an executor that will handle two callback
functions, one to fulfill and one to reject the promise, then it uses the `then`
method to handle result of the previous call, and when it returns it returns a
new pending Promise that it can be used in the same way, all this to allow do
somethig like this:

``` javascript
const myPromise = new Promise(myExecutorFunc)
    .then(handleFulfilledA, handleRejectedA)
    .then(handleFulfilledB, handleRejectedB)
    .then(handleFulfilledC, handleRejectedC);
```

You can provide your custom executor which can be a named function or a lambda:

``` javascript
const promise1 = new Promise((resolve, reject) => {});

function myExecutor(resolve, reject) {}
const promise2 = new Promise(myExecutor);
```

And it also supports handling asynchronus code in inside the Promise executor
without affecting the behaviour of it:

``` javascript
const promise = new Promise((resolve, reject) => {
    setTimeout(() => {
        resolve("WORLD");
    }, 300);
});

promise.then((value) => {
    console.log(value);
});

console.log("HELLO");
```

> Previous code should print `HELLO` and then `WORLD`

## Current Options

With the introduction of C++11 and the aproval of the Thread Support library,
two classes were added to the STL, `std::future` and `std::promise`. The way
this two classes work it's very different from what JavaScript offers.

#### <code>[std::future](https://en.cppreference.com/w/cpp/thread/future)</code>
It's a class that holds a shared state that will be set
asynchronusly in other thread of execution, the biggest issue with this class
is that to retrieve the value you must block the execution of the current
thread:

{{< coderun cpp >}}
#include <iostream>
#include <future>
#include <thread>

int main() {
    std::future<int> f1 = std::async(std::launch::async, [](){
        return 10;
    });

    std::cout << "waiting...\n";
    f1.wait();  // Blocking operation

    std::cout << "f1: " << f1.get() << '\n';
}
{{< /coderun >}}

> `std::future` cannot be set directly but it can be set via created via 
  `std::async` , `std::packaged_task` , or `std::promise`.

#### <code>[std::promise](https://en.cppreference.com/w/cpp/thread/promise)</code>
Provides a similar funcionality to the one that JavaScript
provides but it differs in the way it does it. Internally it contains a future
that can be obtained only once and should be used to retrieve the value set
by the `set_value` or `set_value_at_thread_exit` methods:

{{< coderun cpp >}}
#include <future>
#include <iostream>
#include <numeric>
#include <thread>
#include <vector>

void accumulate(std::vector<int>::iterator first,
                std::vector<int>::iterator last,
                std::promise<int> accumulate_promise) {
    int sum = std::accumulate(first, last, 0);
    accumulate_promise.set_value(sum);  // Notify future
}

int main() {
    std::vector<int> numbers = {1, 2, 3, 4, 5, 6};
    std::promise<int> accumulate_promise;
    std::future<int> accumulate_future = accumulate_promise.get_future();
    std::thread work_thread(accumulate, numbers.begin(), numbers.end(),
                            std::move(accumulate_promise));

    std::cout << accumulate_future.get() << std::endl;  // Blocking operation
    work_thread.join();
}
{{< /coderun >}}

## The Architecture

The current API works in the following way:

#### C++
```c++
std::thread thread;

auto prom = Promise<int>([&thread](auto&& resolve, auto&& reject) {
    thread = std::thread([resolve, reject] {
        std::this_thread::sleep_for(1s);
        resolve(123);
    });
}).then([](const int& value) {
    std::cout << "Value: " << value << std::endl;
}).finally([] {
    std::cout << "Finished" << std::endl;
});

std::cout << "HELLO PROMISE" << std::endl;

thread.join();
```

#### JavaScript
```javascript
const prom = new Promise((resolve, reject) => {
    setTimeout(() => {
        resolve(123);
    }, 1000);
}).then((value) => {
    console.log("Value: " + value);
  	return Promise.resolve(value);
}).finally(() => {
    console.log("Finished");
});

console.log("HELLO PROMISE")
```

As you can see the C++ API is very similar to the one on JavaScript, the biggest
difference is that we have to directly manage the threads that the aplication
uses, in this case join them before finishing.

#### Challenges

The first challenge that I had when developing C++ is an statically typed
language which means that we have to make sure that the Promise we are handling
contains one specific type, this lead the implementation to be heavily
templated.

The second was creating a similar interface to the JavaScript side,
this was tricky as we have to relly heavily on some of the newest C++ features
such as `constexpr` conditionals and `<type_traits>` classes in conjunction with
SFINAE.

The third one was to make sure that the implementation is thread safe. Promises
are usually used for asynchronus tasks, and this requirement should be fulfilled
in order to have a proper implementation.

#### Limitations
Each created promise contains internally an smart `std::shared_ptr` which handles
the shared state of the promise, this means that every new promise that is created
will allocate memory on the heap, also all the callbacks are handled using `std::function`
which might also allocate on this space, so it's adviced not to use this alot on
performance reliant tasks such as rendering loops or update cicles.

#### Creating a Promise

Promise is a templated class so it requires a type to work, and the constructor
should receive a callback that obtain two other fuctions, one to `resolve` the
Promise and one to `reject` it.

```cpp
auto prom = Promise<int>([&thread](auto&& resolve, auto&& reject) {
    resolve(10);
});
```
> The Promise `prom` resolves to `10`

```cpp
auto prom = Promise<int>([&thread](auto&& resolve, auto&& reject) {
    reject("Failed Msg");
});
```
> The Promise `prom` fails with a `"Failed Msg"`

This two functions can be owned by the program and later be called when the
promise fulfills, this can be a network call to get some resources or disk
access to retrieve the content of any file.

Also this two methods are thread safe which means that they can be called by any
async task:

```cpp
auto prom = Promise<int>([&thread](auto&& resolve, auto&& reject) {
    asyncHTTPRequest("URL", resolve);
});
```

##### Promise::then
The `then` method receives a callback, that could be a lambda or a function pointer, this provided callback should receive as arguments a const reference of the value that the Promise resolves to, eg: 
