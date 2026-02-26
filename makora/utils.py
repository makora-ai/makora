# Copyright 2026 Makora Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import os
import sys
import types
from typing import Any, Callable, Iterable, TYPE_CHECKING, Protocol, overload, TypeVar
from typing_extensions import Self
from types import TracebackType, EllipsisType
from functools import lru_cache

from rich.console import Console


U = TypeVar("U", covariant=True)
V = TypeVar("V", covariant=False)


class static_property(property):
    def __init__(
        self,
        fget: Callable[[], Any] | None = None,
        fset: Callable[[Any], None] | None = None,
        fdel: Callable[[], None] | None = None,
        doc: str | None = None,
    ) -> None:
        if fget is not None and not isinstance(fget, staticmethod):
            fget = staticmethod(fget)
        if fset is not None and not isinstance(fset, staticmethod):
            fset = staticmethod(fset)
        if fdel is not None and not isinstance(fdel, staticmethod):
            fdel = staticmethod(fdel)
        super().__init__(fget, fset, fdel, doc)  # type: ignore

    def __get__(self, inst: Any, cls: type | None = None) -> Any:
        if inst is None:
            return self
        if self.fget is None:
            raise AttributeError("unreadable attribute")
        return self.fget.__get__(inst, cls)()  # pylint: disable=no-member

    def __set__(self, inst: Any, val: Any) -> None:
        if self.fset is None:
            raise AttributeError("can't set attribute")

        # pylint: disable=no-member
        return self.fset.__get__(inst)(val)  # type: ignore

    def __delete__(self, inst: Any) -> None:
        if self.fdel is None:
            raise AttributeError("can't delete attribute")
        # pylint: disable=no-member
        return self.fdel.__get__(inst)()  # type: ignore


class LazyModuleType(types.ModuleType):
    def __init__(self, name: str) -> None:
        super().__init__(name)

    def __getattribute__(self, name: str) -> Any:
        _props = super().__getattribute__("_props")
        if name in _props:
            return object.__getattribute__(self, name)
        else:
            return types.ModuleType.__getattribute__(self, name)

    def __dir__(self) -> Iterable[str]:
        ret = super().__dir__()
        ret.extend(self._props)  # type: ignore
        return ret


def add_module_properties(module_name: str, properties: dict[str, Any]) -> None:
    module = sys.modules[module_name]
    replace = False
    if isinstance(module, LazyModuleType):
        hacked_type = type(module)
    else:
        hacked_type = type(
            "LazyModuleType__{}".format(module_name.replace(".", "_")),
            (LazyModuleType,),
            {"_props": set()},
        )
        replace = True

    for name, prop in properties.items():
        if not isinstance(prop, property):
            prop = property(prop)
        setattr(hacked_type, name, prop)
        hacked_type._props.add(name)  # type: ignore

    if replace:
        new_module = hacked_type(module_name)
        spec = getattr(module, "__spec__", None)
        module.__class__ = new_module.__class__
        module.__name__ = new_module.__name__
        module.__dict__.update(new_module.__dict__)
        module.__spec__ = spec


_env_vars: dict[str, "EnvVar"] = {}


class EnvVarMeta(type):
    def __call__(self, var_name: str, default: str | None = None, hidden: bool = False) -> "EnvVar":
        current = _env_vars.get(var_name)
        if current is not None:
            if current.default == default:
                return current
            raise RuntimeError(
                f"Environment variable with name: {var_name!r} already "
                f"registered with default value of: {current.default!r}"
            )

        new = super().__call__(var_name, default, hidden)
        assert isinstance(new, EnvVar)
        _env_vars[var_name] = new
        return new


class EnvVar(metaclass=EnvVarMeta):
    def __init__(self, var_name: str, default: str | None, hidden: bool = False) -> None:
        self.var_name = var_name
        self.default = default
        self.hidden = hidden
        self._resolved = False
        self._value: str | None = None

    @property
    def value(self) -> str:
        if not self._resolved:
            self._value = os.environ.get(self.var_name, self.default or "")
            self._resolved = True

        assert isinstance(self._value, str)
        return self._value


def get_env_vars() -> Iterable[EnvVar]:
    return sorted(_env_vars.values(), key=lambda e: e.var_name)


NO_RICH = EnvVar("MAKORA_NO_RICH", "")


@lru_cache(maxsize=1, typed=False)
def get_rich_console() -> Console:
    if bool(NO_RICH.value):
        return Console(
            color_system=None,
            force_terminal=False,
            force_interactive=False,
            no_color=True,
            tab_size=4,
            highlight=False,
            emoji=False,
        )

    return Console(
        tab_size=4,
    )


class _dummy_context:
    def __init__(self, value: Any = ...) -> None:
        self.value = value

    def __enter__(self) -> Any:
        if self.value is Ellipsis:
            return self
        return self.value

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        return None


class _async_dummy_context:
    def __init__(self, value: Any = ...) -> None:
        self.value = value

    async def __aenter__(self) -> Any:
        if self.value is Ellipsis:
            return self
        return self.value

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        return None


if TYPE_CHECKING:

    class SelfContext(Protocol):
        def __enter__(self) -> Self: ...

        def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_val: BaseException | None,
            exc_tb: TracebackType | None,
        ) -> bool | None: ...

    class ValueContext(Protocol[U]):
        def __enter__(self) -> U: ...

        def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_val: BaseException | None,
            exc_tb: TracebackType | None,
        ) -> bool | None: ...

    class SelfAsyncContext(Protocol):
        async def __aenter__(self) -> Self: ...

        async def __aexit__(
            self,
            exc_type: type[BaseException] | None,
            exc_val: BaseException | None,
            exc_tb: TracebackType | None,
        ) -> bool | None: ...

    class ValueAsyncContext(Protocol[U]):
        async def __aenter__(self) -> U: ...

        async def __aexit__(
            self,
            exc_type: type[BaseException] | None,
            exc_val: BaseException | None,
            exc_tb: TracebackType | None,
        ) -> bool | None: ...

    @overload
    def dummy_context(value: EllipsisType = ...) -> SelfContext: ...

    @overload
    def dummy_context(value: V) -> ValueContext[V]: ...

    def dummy_context(value: Any = ...) -> SelfContext | ValueContext[Any]:
        return _dummy_context(value)

    @overload
    def async_dummy_context(value: EllipsisType = ...) -> SelfAsyncContext: ...

    @overload
    def async_dummy_context(value: V) -> ValueAsyncContext[V]: ...

    def async_dummy_context(
        value: Any = ...,
    ) -> SelfAsyncContext | ValueAsyncContext[Any]:
        return _async_dummy_context(value)
else:

    def dummy_context(value=...):
        return _dummy_context(value)

    def async_dummy_context(value=...):
        return _async_dummy_context(value)
