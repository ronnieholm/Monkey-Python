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
        found = name in self._store.keys()
        obj = None
        if found:
            obj = self._store[name]
        elif self.outer is not None:
            # If current environment doesn't have a value associated with a
            # name, we recursively call get on enclosing environment (which the
            # current environment is extending) until either name is found or
            # caller can issue a "unknown identifier" error.
            obj, found = self.outer.get(name)
        return obj, found

    def set(self, name: str, value: "Object") -> "Object":
        self._store[name] = value
        return value
