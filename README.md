#SimpleIoC

SimpleIoC is a python3 inversion of control container. Concept coined by http://www.martinfowler.com/articles/injection.html

Example usage
```
import simpleioc
import example

container = Container()
# singletons
container.register(example.Singleton, 'singleton')
# instanced
container.register_instance(example.library)
container.register_instance(example.anyType)

# usage container to resolve types and their contructors
container.resolve_by_type(example.require_all)
```

## Registration types
```
temporal = "New instance for every resolve",
singleton = "Only one instance ever, lazy constructed",
weak_reference = "Similar to singleton but object instance can be " \
                 "released if no usage is taking place before collection ",
thread_local = "Effectively singleton per thread. Useful for non-thread " \
               "safe code."
```


#Building
Developed with python3.5 on mac/linux

Strongly recommend usage of virtualenv

```
pip3 install virtualenv
virtualenv --python=python3 . 
source bin/activate
```

Uses open source pybuilder as build script, in-lue of different tools for 
dependency/packaging/testing/coverage etc.

```
pip install pybuilder
```

First run will download the world and can take minutes to install dependencies.
Once done will lint, unit tests, and package.

```
pyb
```

Bin Packaging; Not tested...

```
target/dist/simpleioc*/setup.py
```

**IDE support included**
PyCharms or other IDE project files are generated....

```
pyb pycharm_generate
```


