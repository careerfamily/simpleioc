from threading import Thread
import unittest
import gc
from rodenioc import Container, RegistrationUsage, RegistrationNotFoundError


class ContainerTests(unittest.TestCase):
    def test_resolve_by_string(self):
        c = Container()
        c.register(Foo, 'foo')
        c.register(Bar)

        result = c.resolve_by_type(StringAnnotated)
        self.assertIsInstance(result, StringAnnotated)
        self.assertIsInstance(result.bar, Bar)
        self.assertIsInstance(result.foo, Foo)

    def test_resolve_by_names(self):
        c = Container()
        c.register(Foo, 'foo')
        c.register(Bar)

        result = c.resolve_by_type(NoAnnotated)
        self.assertIsInstance(result, NoAnnotated)
        self.assertIsInstance(result.bar, Bar)
        self.assertIsInstance(result.foo, Foo)

    def test_resolve_by_types(self):
        c = Container()
        c.register(Foo, Foo)
        c.register(Bar, Bar)

        result = c.resolve_by_type(TypeAnnotated)
        self.assertIsInstance(result, TypeAnnotated)
        self.assertIsInstance(result.bar, Bar)
        self.assertIsInstance(result.foo, Foo)

    def test_resolve_all_by_name(self):
        c = Container()
        c.register(Foo, 'foo')
        c.register(Bar)
        c.register(StringAnnotated, 'target')

        result = c.resolve_by_key('target')
        self.assertIsInstance(result, StringAnnotated)
        self.assertIsInstance(result.bar, Bar)
        self.assertIsInstance(result.foo, Foo)

    def test_resolve_singletons(self):
        c = Container()
        c.register(Foo, 'foo').usage = RegistrationUsage.singleton
        c.register(Bar).usage = RegistrationUsage.singleton
        c.register(StringAnnotated, 'target')
        result = c.resolve_by_key('target')

        result_id = id(result)
        foo_id = id(result.foo)
        bar_id = id(result.bar)

        result2 = c.resolve_by_key('target')

        self.assertNotEquals(result_id, id(result2))
        self.assertEquals(foo_id, id(result2.foo))
        self.assertEquals(bar_id, id(result2.bar))

    def test_resolve_weak(self):
        """
            Can theoretically false negative as id can assign to new instances
            after collection
        """
        c = Container()
        c.register(Foo, 'foo').usage = RegistrationUsage.weak_reference
        c.register(Bar).usage = RegistrationUsage.weak_reference
        c.register(StringAnnotated, 'target')
        result = c.resolve_by_key('target')

        result_id = id(result)
        foo_id = id(result.foo)
        bar_id = id(result.bar)

        result2 = c.resolve_by_key('target')

        self.assertNotEquals(result_id, id(result2))
        self.assertEquals(foo_id, id(result2.foo))
        self.assertEquals(bar_id, id(result2.bar))

        del result
        del result2

        gc.collect()

        self.assertNotEquals(foo_id, c.resolve_by_key('foo'))
        self.assertNotEquals(bar_id, c.resolve_by_key('bar'))

    def test_resolve_thread_local(self):
        c = Container()
        c.register(Foo, 'foo').usage = RegistrationUsage.thread_local
        c.register(Bar).usage = RegistrationUsage.thread_local
        c.register(Bar, 'bar2').usage = RegistrationUsage.singleton
        c.register(StringAnnotated, 'target')
        result = c.resolve_by_key('target')

        result_id = id(result)
        foo_id = id(result.foo)
        bar_id = id(result.bar)
        bar2_id = id(c.resolve_by_key('bar2'))

        result2 = c.resolve_by_key('target')

        self.assertNotEquals(result_id, id(result2))
        self.assertEquals(foo_id, id(result2.foo))
        self.assertEquals(bar_id, id(result2.bar))
        assert_not_equals = self.assertNotEquals
        assert_equals = self.assertEquals

        class ThreadWorker(Thread):
            def run(self):
                assert_not_equals(foo_id, id(c.resolve_by_key('foo')))
                assert_not_equals(bar_id, id(c.resolve_by_key('bar')))
                assert_equals(bar2_id, id(c.resolve_by_key('bar2')))

        thread = ThreadWorker()
        thread.start()
        thread.join()

    def test_resolve_defaults(self):
        c = Container()
        c.register(Foo, 'foo')
        c.register(Bar)
        c.register(DefaultNoAnnotated, 'target')
        result = c.resolve_by_key('target')

        self.assertIsInstance(result, DefaultNoAnnotated)
        self.assertEquals(1, result.default)

    def test_resolve_not_found(self):
        c = Container()
        c.register(DefaultNoAnnotated, 'target')
        with self.assertRaises(RegistrationNotFoundError):
            c.resolve_by_key('target')

    def test_resolve_instance(self):
        foo = Foo()

        c = Container()
        c.register_instance(foo, 'foo')
        c.register(Bar)
        c.register(StringAnnotated, 'target')
        result = c.resolve_by_key('target')

        self.assertIsInstance(result, StringAnnotated)
        self.assertEquals(id(foo), id(result.foo))

        result2 = c.resolve_by_type(NoAnnotated)

        self.assertIsInstance(result2, NoAnnotated)
        self.assertEquals(id(foo), id(result2.foo))




class Foo:
    pass


class Bar:
    pass


class StringAnnotated:
    def __init__(self, foo: 'foo', bar: 'bar'):
        self.foo = foo
        self.bar = bar


class NoAnnotated:
    def __init__(self, foo, bar):
        self.foo = foo
        self.bar = bar


class TypeAnnotated:
    def __init__(self, foo: Foo, bar: Bar):
        self.foo = foo
        self.bar = bar


class DefaultNoAnnotated:
    def __init__(self, foo, bar, default=1):
        self.default = default
        self.foo = foo
        self.bar = bar
