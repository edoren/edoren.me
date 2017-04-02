---
categories: ["Tutorials", "C++", "Linux"]
date: 2017-04-01T18:45:08-05:00
tags: []
title: Entendiendo el Linkeo en Tiempo de Ejecución en C/C++
type: other
---

Si has llegado a usar C o C++ de seguro alguna vez ha tenido la necesidad de hacer uso de metodos que le faciliten tu trabajo, a nadie le gusta re inventar la rueda (a menos que seas un cavernicola). Y es que muchas veces nos encontramos con casos en los que tenemos que hacer el calculo de una raiz cuadrada con `sqrt`, o simplemente queremos usar `printf` para imprimir un mensaje en la pantalla.

Y si, cada vez que incluimos estos archivos estamos haciendo uso de una Libreria [^1], ya sea la Libreria estandard de C o C++, o alguna otra de la infinidad que existen en Internet.

Estas Librerias lo que hacen es unirse como parte del código de nuestro ejecutable por medio de una operacion llamada Linking [^2]. Hay dos maneras en las que podemos realizar este proceso, en tiempo de compilación y en tiempo de ejecución.

Por motivos de esta guia vamos a enfocarnos en la segunda, pero aún así voy a explicar como el compilador realiza este proceso.

## En Tiempo de Compilación
Si haces uso de Linux y alguna vez has compilado desde la consola algún programa que use hilos, te sonará el siguiente comando:
```bash
gcc miprograma.c -o miprograma -lpthread
```
¿Te suena?, bueno pues en este caso estamos haciendo Linking compilación. Al agregar la linea `-lpthread` le estamos diciendo al compilador que vamos a hacer uso de una libreria llamada **pthread**, la cual es la libreria de POSIX para el manejo de hilos [^3].

Lo que el compilador realiza al agregar esta linea es que busca en ciertos directorios del sistema si se encuentra dicha librería para posteriomente resolver todos los simbolos (funciones, variables o objetos) que use de ella. En Linux busca archivos del tipo _lib**nombre**.so_ o _lib**nombre**.a_ para librerias dinámicas y estáticas respectivamente. En este caso en especifico hace uso de la libreria _**libpthread.so**_.

## En Tiempo de Ejecución
La otra alternativa para poder hacer uso de estas librerias, es cargandolas en tiempo ejecución, en la cual haciendo de librerías dinámicas (`.so` en Linux, `.dll` en Windows o `.dylib` en Mac OSX).

Para poder hacer esto tenemos que hacer uso de librerías del sistema, en este caso haremos uso del encabezado `<dlfcn.h>` que podemos encontrar en Linux y Mac OSX. En Windows hay alternativa similar que se encuentra en el encabezado `<windows.h>` [^4].

### Creando nuestra primera librería
Lo primero que haremos es crear una librería dinámica que nos sirva de ejemplo. Para eso usaremos el siguiente código:
```c++
#include "HelloLibrary.hpp"
#include <iostream>

void SayHello(const char* name) {
    std::cout << "Hello " << name << " have a nice day!" << std::endl;
}
```
Archivo _HelloLibrary.cpp_

Lo que acabamos de hacer es una funcion que dado una cadena que le pasemos va a imprimir un mensaje de saludo. Si observamos incluye un archivo llamado _**HelloLibrary.hpp**_ el cual tiene el siguiente contenido:
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
Archivo _HelloLibrary.hpp_

Ahora vamos a compilar y generar nuestra librería dinámica, para eso ejecutamos el siguiente comando:
```bash
g++ HelloLibrary.cpp -o libHelloLibrary.so -shared -fPIC
```
> NOTA: Si estas en Ubuntu o Debian probablemente debas ejecutar el comando `sudo apt-get install build-essential` para instalar el compilador de C y C++

¿Que acaba de pasar acá?, bueno, le estamos diciendo al compilador que queremos compilar el archivo _**HelloLibrary.cpp**_ y generar una librería llamada _**HelloLibrary.so**_, adicionalmente le pasamos dos parametros más, `-shared` le indica al compilador que queremos hacer un objeto compartido que posteriormente pueda ser Linkeado con otros objetos para crear un ejcutable, `-fPIC` que le dice al compilador que genere código de posición independiente (position-independent code PIC)[^5] el cual es nesario para crear la librería dinámica.

### Usando nuestra librería
Ahora hemos generado nuestra primera librería, ¿pero como hacemos uso de ella?. Para esto vamos a hacer uso de la funciones `dlopen`, `dlclose` y `dlsym` las cuales tienen la siguiente definición:
```c++
void* dlopen(const char* filename, int flag);
int dlclose(void* handle);
void* dlsym(void* handle, const char* symbol);
```
> Podemos leer más de estas funciones en los manuales de Linux, ejecutando el comando `man [funcion]`. Ej `man dlopen`.

Necesitamos cargar la libraría que creamos en nuestro programa, para esto haremos uso de `dlopen`:
```c++
void* handle = dlopen("libHelloLibrary.so", RTLD_LAZY);
```

A la hora de cargar una librería, Linux hace una busqueda en ciertos lugares en la siguiente forma:

1. Mira si la librería se encuentra al lado del ejecutable que la llamó
2. Busca en la variable de entorno LD_LIBRARY_PATH por directios adicionales en los cuales se pueda encontrar
3. Busca en las librerias del sistema

Como en nuestro caso la librería se encontrará al lado de nuestro ejecutable no tendremos ningún problema. Si la funcion se ejecuta correctamente `handle` va a tener almacenada nuestra librería. Si falla devolvera `NULL`.

Ahora vamos a cargar la funcion `SayHello` que declaramos anteriormente, haciendo uso de `dlsym` de la siguiente forma:
```
PFN_SAY_NAME hello = (PFN_SAY_NAME)dlsym(handle, "SayHello");
```

Wow, wow!, ¿que pasó acá?, ¿que es ese tipo `PFN_SAY_NAME`?. Ya que `dlsym` devuelve un puntero de tipo `void*`, y lo que necesitamos cargar es un puntero a una funcion debemos tener un tipo que nos permita decir que funcion es (que parametros requiere y que valor devuelve), para esto lo declaramos así:
```c++
typedef void (*PFN_SAY_NAME)(const char*);

// En C++11 esto se puede hacer más facil
using PFN_SAY_NAME = decltype(&SayHello);
```

Ya solo queda llamar a nuestra funcion y cerrar nuestra librería:
```c++
hello("JointDeveloper");
dlclose(handle);
```

#### Todo junto:
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

    PFN_SAY_NAME hello = (PFN_SAY_NAME)dlsym(handle, "SayHello");
    if (!hello) {
        std::cout << "Could not find symbol SayHello" << std::endl;
        dlclose(handle);
        return 1;
    }

    hello("JointDeveloper");
    dlclose(handle);

    return 0;
}
```
Archivo _LoadLibrary.cpp_

Adicionalmente he agregado código para verificar posibles errores que surjan al cargar la librería. 

Finalmente compilamos y ejecutamos nuestro código de la siguiente forma:
```bash
g++ -std=c++11 LoadLibrary.cpp -o LoadLibrary.bin -ldl
./LoadLibrary.bin
```

Si miras bien el comando de compilacion estamos haciendo uso de la libreria `dl` esta librería contiene las funciones que anteriormente utilizamos.

---
Si has llegado hasta acá espero que esta guia te haya sido de utilidad y pudieras entender de manera clara lo explicado. El código completo lo puedes encontrar en el siguiente repositorio de [GitHub](https://github.com/edoren/BlogCodes/tree/master/dynamic_library_loading_cpp)

[^1]: [https://en.wikipedia.org/wiki/Library_(computing)](https://en.wikipedia.org/wiki/Library_(computing))
[^2]: [https://en.wikipedia.org/wiki/Linker_(computing)](https://en.wikipedia.org/wiki/Linker_(computing))
[^3]: [https://en.wikipedia.org/wiki/POSIX_Threads](https://en.wikipedia.org/wiki/POSIX_Threads)
[^4]: [https://msdn.microsoft.com/en-us/library/windows/desktop/ms684175(v=vs.85).aspx](https://msdn.microsoft.com/en-us/library/windows/desktop/ms684175(v=vs.85).aspx)
[^5]: [https://en.wikipedia.org/wiki/Position-independent_code](https://en.wikipedia.org/wiki/Position-independent_code)
