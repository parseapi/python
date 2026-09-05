"""Record the reviewed Python calling interface, without making requests."""
import inspect
import json
from pathlib import Path
from parseapi import AsyncParseAPI, ParseAPI, ParseAPIError


def signature(call):
    params = []
    for p in inspect.signature(call).parameters.values():
        if p.name == 'self':
            continue
        entry = {'name': p.name, 'kind': p.kind.name}
        if p.default is not inspect.Parameter.empty:
            entry['default'] = p.default
        if p.annotation is not inspect.Parameter.empty:
            entry['type'] = p.annotation if isinstance(p.annotation, str) else str(p.annotation)
        params.append(entry)
    result = {'async': inspect.iscoroutinefunction(call), 'parameters': params}
    returns = inspect.signature(call).return_annotation
    if returns is not inspect.Signature.empty:
        result['returns'] = returns if isinstance(returns, str) else str(returns)
    return result


def snapshot():
    result = {}
    for cls in (ParseAPI, AsyncParseAPI):
        surface = {'constructor': signature(cls)}
        client = cls('signature_fixture')
        try:
            for name in sorted(n for n in dir(client) if not n.startswith('_')):
                member = getattr(client, name)
                if callable(member):
                    surface[name] = signature(member if inspect.ismethod(member) else member.__call__)
                    if not inspect.ismethod(member):
                        for child in sorted(n for n in dir(member) if not n.startswith('_')):
                            method = getattr(member, child)
                            if callable(method):
                                surface[name + '.' + child] = signature(method)
            result[cls.__name__] = surface
        finally:
            if cls is ParseAPI:
                client.close()
            else:
                import asyncio
                asyncio.run(client.close())
    result['ParseAPIError'] = signature(ParseAPIError)
    return result


if __name__ == '__main__':
    import sys
    path = Path(__file__).resolve().parents[1] / 'api/public.json'
    actual = json.dumps(snapshot(), indent=2, sort_keys=True) + '\n'
    if '--write' in sys.argv:
        path.write_text(actual)
        print('Wrote the reviewed public API baseline.')
    elif path.read_text() != actual:
        raise SystemExit('Public API changed. Review the diff, then run PYTHONPATH=src python scripts/public_api.py --write.')
    else:
        print('Public API matches its reviewed baseline.')
