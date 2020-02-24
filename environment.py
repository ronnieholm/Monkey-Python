from typing import Dict


class Environment:
    def __init__(self):
        self._store: Dict[str, "Object"] = {}
        self.outer: Environment = None

    @staticmethod
    def new_enclosed_environment(outer: "Environment") -> "Environment":
        env = Environment()
        env.outer = outer
        return env

    def get(self, name: str) -> "Optional[(Object, bool)]":
        ok = name in self._store.keys()
        obj = None
        if ok:
            obj = self._store[name]
        elif self.outer != None:
            # If current environment doesn't have a value associated with a
            # name, we recursively call get on enclosing environment (which the
            # current environment is extending) until either name is found or
            # caller can issue a "unknown identifier" error.
            obj, ok = self.outer.get(name)
        return obj, ok

    def set(self, name: str, value: "Object") -> "Object":
        self._store[name] = value
        return value
