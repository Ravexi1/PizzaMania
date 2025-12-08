def test_asgi_application_imports():
    """Ensure ASGI application can be imported without raising errors."""
    import importlib
    mod = importlib.import_module('PizzaMania.asgi')
    assert hasattr(mod, 'application')
