from typing import Dict, Optional, Tuple


class Environment:
    def __init__(self) -> None:        
        self._store: Dict[str, "monkey_object.MonkeyObject"] = {}
        self.outer: Optional[Environment] = None

    @staticmethod
    def new_enclosed_environment(outer: "Environment") -> "Environment":
        env = Environment()
        env.outer = outer
        return env

    def get(self, name: str) -> "Optional[monkey_object.MonkeyObject]":
        found = name in self._store.keys()
        obj = None
        if found:
            obj = self._store[name]
        elif self.outer is not None:
            # If current environment doesn't have a value associated with a
            # name, we recursively call get on enclosing environment (which the
            # current environment is extending) until either name is found or
            # caller can issue a "unknown identifier" error.
            obj = self.outer.get(name)
        return obj

    def set(self, name: str, value: "monkey_object.MonkeyObject") -> "monkey_object.MonkeyObject":
        self._store[name] = value
        return value

import monkey_object