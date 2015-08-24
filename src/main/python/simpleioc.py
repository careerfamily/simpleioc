from enum import Enum
from inspect import signature, Parameter
import threading
from weakref import WeakValueDictionary


class RegistrationUsage(Enum):
    temporal = "New instance for every resolve",
    singleton = "Only one instance ever, lazy constructed",
    weak_reference = "Similar to singleton but object instance can be " \
                     "released if no usage is taking place before collection ",
    thread_local = "Effectively singleton per thread. Useful for non-thread " \
                   "safe code."


class Registration:
    """
        DTO/configuration object
    """

    def __init__(self, type_ref: type):
        self.type_ref = type_ref
        self._usage = RegistrationUsage.temporal

    @property
    def usage(self):
        return self._usage

    @usage.setter
    def usage(self, usage: RegistrationUsage):
        self._usage = usage


class RegistrationError(Exception):
    pass


class RegistrationNotFoundError(RegistrationError):
    def __init__(self, missing):
        self.missing = missing


class Container:
    """
        Container used for registering and resolving components. Ideally no
        component will depend on a reference to the container.
    """

    def __init__(self):
        self._key_to_registration = dict()
        self._singleton_instances = dict()
        self._singleton_instances_lock = threading.Lock()
        self._weak_references = WeakValueDictionary()
        self._weak_references_lock = threading.Lock()
        self._thread_local = threading.local()

    def register_instance(self, instance: object, register_key=None):
        key = register_key if register_key else instance.__name__.lower()
        registration = Registration(instance.__class__)
        registration.usage = RegistrationUsage.singleton
        self._key_to_registration[key] = registration
        with self._singleton_instances_lock:
            self._singleton_instances[key] = instance

    def register(self, type_ref: type, register_key=None) -> Registration:
        key = register_key if register_key else type_ref.__name__.lower()
        registration = Registration(type_ref)
        self._key_to_registration[key] = registration
        return registration

    def resolve_by_type(self, type_ref: type):
        reg = Registration(type_ref)
        return self.__get_instance_for("type::"+type_ref.__name__.lower(), reg)

    def resolve_by_key(self, register_key):
        try:
            found = self._key_to_registration[register_key]
        except KeyError:
            raise RegistrationNotFoundError(register_key)
        return self.__get_instance_for(register_key, found)

    def __resolve_by_parameter(self, parameter: Parameter):
        try:
            if parameter.annotation != Parameter.empty:
                return self.resolve_by_key(parameter.annotation)
            return self.resolve_by_key(parameter.name.lower())
        except RegistrationNotFoundError:
            # fixme non registered defaults are expensive...
            if parameter.default is Parameter.empty:
                raise
            return parameter.default

    def __get_instance_for(self, cache_key, registration: Registration):
        def create_func():
            params = signature(registration.type_ref).parameters
            args = {name: self.__resolve_by_parameter(param)
                    for name, param in params.items()}
            return registration.type_ref(**args)

        if registration.usage is RegistrationUsage.temporal:
            return create_func()
        elif registration.usage is RegistrationUsage.singleton:
            return self.__get_singleton(cache_key, create_func)
        elif registration.usage is RegistrationUsage.weak_reference:
            return self.__get_weak(cache_key, create_func)
        elif registration.usage is RegistrationUsage.thread_local:
            return self.__get_thread_local(cache_key, create_func)

    def __get_weak(self, cache_key, create_func):
        result = self._weak_references.get(cache_key, None)
        if result is not None:
            return result
        with self._weak_references_lock:
            result = self._weak_references.get(cache_key, None)
            if result is not None:
                return result
            result = create_func()
            self._weak_references[cache_key] = result
            return result

    def __get_singleton(self, cache_key, create_func):
        if cache_key in self._singleton_instances:
            return self._singleton_instances[cache_key]
        with self._singleton_instances_lock:
            if cache_key in self._singleton_instances:
                return self._singleton_instances[cache_key]
            result = create_func()
            self._singleton_instances[cache_key] = result
            return result

    def __get_thread_local(self, cache_key, create_func):
        local = self._thread_local
        if 'registration_dictionary' not in local.__dict__:
            local.registration_dictionary = dict()
        if cache_key in local.registration_dictionary:
            return local.registration_dictionary[cache_key]
        result = create_func()
        local.registration_dictionary[cache_key] = result
        return result
