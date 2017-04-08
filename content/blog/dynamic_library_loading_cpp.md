---
date: 2017-04-01T18:45:08-05:00
categories: [Tutorials]
tags: [C++, Linux]
title: Understanding Dynamic Linking in C++
description: What is and how to use dynamic linking in C++
type: blog
---

If you've ever used C or C ++ for sure you've had to use methods that make your job easier, no one likes to re-invent the wheel (unless you're a caveman). And is that many times we find cases where we have to do the calculation of a square root with `sqrt`, or we just want to use ` printf` to print a message on the screen.

<!--more-->

Each time we include this files we are making use of one Library [^1], either the C or C++ standard library, or some other of the infinity of libraries that exist on the Internet

What this libraries do is join as part of the code of our executable by means of and operation called Linking [^2]. There are two ways we can perform this process, in compiling time and in run time.

For reasons of this tutorial we will focus on the second one, but I will still explain how the compiler perform this process.

## In Compile Time
If use Linux and have ever compiled from the console any program that uses threads, you will know the following command:
```bash
gcc miprograma.c -o miprograma -lpthread
```
Do you recognize it?, well in this case what we are doing is linking a library in compile time. When we add the `-lpthread` line we are telling the compiler that we are going to use a library called **pthread**, which is the POSIX library for handling threads [^3].

What the compiler does when adding this line is that it search in certain directories of the system if that library is found to later resolve al the symbols (functions, variables, or objects) used by it. In Linux it searchs for files of the form _lib**name**.so_ or _lib**name**.a_ for dynamic and static libraries respectively. In this speficic case it uses the library _**libpthread.so**_.

## In Run Time
Another alternative to make use this libraries, is loading them in run time, through dynamic libraries (`.so` in Linux, `.dll` in Windows or `.dylib` in Mac OS X).

In order to do this we have to make use of libraries that the system provides, in this case we will make use of the header `<dlfcn.h>` that we can find in Linux and Mac OSX. In Windows there is similar alternative that is found in the header`<windows.h>` [^4].

### Creating Our First Library
The first thing we are going to do is create a dynamic library that will serve as an example. For that we will use the following code:
```c++
#include "HelloLibrary.hpp"
#include <iostream>

void SayHello(const char* name) {
    std::cout << "Hello " << name << " have a nice day!" << std::endl;
}
```
File _HelloLibrary.cpp_

What we have just done is create function that given a string it's going to print a greeting message. If we take a look at the code we will se that is includes a file called _**HelloLibrary.hpp**_ which has the following content:
```c++
#pragma once

#ifdef  __cplusplus
extern "C" {
#endif

void SayHello(const char* name);

#ifdef  __cplusplus
}
#endif
```
File _HelloLibrary.hpp_

Now we are going to compile and generate our own dynamic library:
```bash
g++ HelloLibrary.cpp -o libHelloLibrary.so -shared -fPIC
```
> NOTE: If you are in Ubuntu or Debian you should probably execute the following command in order to install the C and C++ compiler: `sudo apt-get install build-essential`

What just happened here?, well, we are telling the compiler that we want to compile the file _**HelloLibrary.cpp**_ and generate a library called _**HelloLibrary.so**_, additionaly we are providing two more parameters, `-shared` tells the compiler that we want to create a shared object which can later be linked with other objects to form an executable, `-fPIC` tells the compiler to emit position-independent code (PIC)[^5] which is necessary to create a dynamic library.

### Using Our Library
Now have just generated our first library, but how do we use it?. We are going to make use of the functions `dlopen`, `dlclose` y `dlsym` which have the following definition:
```c++
void* dlopen(const char* filename, int flag);
int dlclose(void* handle);
void* dlsym(void* handle, const char* symbol);
```
> We can read more about this libraries in the Linux manuals, by executing the command `man [función]`. E.g. `man dlopen`.

We need to load the library we created in our program, for this we are will use of `dlopen`:
```c++
void* handle = dlopen("libHelloLibrary.so", RTLD_LAZY);
```

If this function executes correctly `handle` will point to our librería, if it fails it will be set to `NULL`.

Now we are going to load the function `SayHello` that we declared early, using `dlsym` as follows:
```c++
PFN_SAY_NAME hello = reinterpret_cast<PFN_SAY_NAME>(dlsym(handle, "SayHello"));
```

Wow, wow!, what just happened?, what is that type `PFN_SAY_NAME`?. Since `dlsym` returns a pointer of type `void*`, and what we need is a pointer to a function, we must have a type that allows us detect what function we are pointing to (what parameters it requires and what does it returns), to do so we declare this type as follows:
```c++
typedef void (*PFN_SAY_NAME)(const char*);

// In C++11 it's easier if you have the function declaration
using PFN_SAY_NAME = decltype(&SayHello);
```

Now we just have to call our function and close our library:
```c++
hello("Edoren");
dlclose(handle);
```

#### All Together:
```c++
#include "HelloLibrary.hpp"
#include <iostream>
#include <dlfcn.h>

typedef void (*PFN_SAY_NAME)(const char*);

int main(void) {
    void* handle = dlopen("libHelloLibrary.so", RTLD_LAZY);
    if (!handle) {    
        std::cout << "Could not open the math library" << std::endl;
        return 1;
    }

    PFN_SAY_NAME hello = reinterpret_cast<PFN_SAY_NAME>(dlsym(handle, "SayHello"));
    if (!hello) {
        std::cout << "Could not find symbol SayHello" << std::endl;
        dlclose(handle);
        return 1;
    }

    hello("Edoren");
    dlclose(handle);

    return 0;
}
```
File _LoadLibrary.cpp_

Additionaly I added some code to verify posible errors that could arise.

Finally we copile and execute our code as follows:
```bash
g++ -std=c++11 LoadLibrary.cpp -o LoadLibrary.bin -ldl
./LoadLibrary.bin
```

If you look carefully at the compilation command we are making use of the `dl` library which contains the functions we previously used.

If you have reached this part I hope that this tutorial has been useful and you could have clearly understood the concept. You can find the source code of this tutorial on my [GitHub](https://github.com/edoren/BlogCodes/tree/master/dynamic_library_loading_cpp) repository

[^1]: [https://en.wikipedia.org/wiki/Library_(computing)](https://en.wikipedia.org/wiki/Library_(computing))
[^2]: [https://en.wikipedia.org/wiki/Linker_(computing)](https://en.wikipedia.org/wiki/Linker_(computing))
[^3]: [https://en.wikipedia.org/wiki/POSIX_Threads](https://en.wikipedia.org/wiki/POSIX_Threads)
[^4]: [https://msdn.microsoft.com/en-us/library/windows/desktop/ms684175(v=vs.85).aspx](https://msdn.microsoft.com/en-us/library/windows/desktop/ms684175(v=vs.85).aspx)
[^5]: [https://en.wikipedia.org/wiki/Position-independent_code](https://en.wikipedia.org/wiki/Position-independent_code)
