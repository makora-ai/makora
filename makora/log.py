import sys
import logging
from contextlib import contextmanager
from types import EllipsisType
from typing import Any, MutableMapping, Generator, overload, TypeVar, TypeAlias, TYPE_CHECKING
from inspect import getfullargspec

from .utils import EnvVar, get_rich_console

DEBUG = EnvVar("MAKORA_DEBUG", "0", desc="Turns on debug logging when set to '1'.")
T = TypeVar("T")
MAX_LOC_CHARS = 32

LEVEL_TO_COLOR = {
    logging.DEBUG: ("[dim]", "[/dim]"),
    logging.INFO: ("", ""),
    logging.WARNING: ("[yellow]", "[/yellow]"),
    logging.ERROR: ("[red]", "[/red]"),
    logging.CRITICAL: ("[bold][red]", "[/red][/bold]"),
}


if TYPE_CHECKING:
    BaseAdapterType: TypeAlias = logging.LoggerAdapter[logging.Logger]
    LoggerOrAdapterType: TypeAlias = logging.Logger | logging.LoggerAdapter[logging.Logger]
else:
    BaseAdapterType: TypeAlias = logging.LoggerAdapter
    LoggerOrAdapterType: TypeAlias = logging.Logger | logging.LoggerAdapter


class RichHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.console = get_rich_console()

    def flush(self) -> None:
        assert self.lock is not None
        with self.lock:
            sys.stdout.flush()

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            self.console.print(msg)
            self.flush()
        except Exception:
            self.handleError(record)


class RichFormatter(logging.Formatter):
    def usesTime(self) -> bool:
        return True

    def formatMessage(self, record: logging.LogRecord) -> str:
        cbeg, cend = LEVEL_TO_COLOR.get(record.levelno, ("", ""))
        locinfo = f"{record.module}:{record.lineno}"
        if len(locinfo) > MAX_LOC_CHARS:
            locinfo = "..." + locinfo[len(locinfo) - (MAX_LOC_CHARS - 3) :]
        msg = f"[dim]{record.asctime}[/dim] | {cbeg}{record.levelname:>9} | {locinfo} | {record.message}{cend}"
        return msg


class BraceMessage:
    def __init__(self, fmt: Any, args: tuple[Any], kwargs: dict[str, Any]):
        self.fmt = fmt
        self.args = args
        self.kwargs = kwargs

    def __str__(self) -> str:
        if not self.args and not self.kwargs:
            return str(self.fmt)

        return str(self.fmt).format(*self.args, **self.kwargs)

    def __repr__(self) -> str:
        return super().__repr__() + self.__str__()


class BraceStyleAdapter(BaseAdapterType):
    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def log(self, level: int, msg: Any, *args: Any, **kwargs: Any) -> None:
        to_use: Any | BraceMessage = msg
        if self.isEnabledFor(level):
            if not isinstance(msg, BraceMessage):
                msg, log_kwargs = self.process(msg, kwargs)
                to_use = BraceMessage(msg, args, kwargs)
            else:
                assert not args
                log_kwargs = kwargs

            self.logger._log(level, to_use, (), **log_kwargs, stacklevel=2)

    def process(self, msg: str, kwargs: MutableMapping[str, Any]) -> tuple[str, dict[str, Any]]:
        log_kwargs = {key: kwargs[key] for key in getfullargspec(self.logger._log).args[1:] if key in kwargs}
        return msg, log_kwargs


def configure_logger(debug: bool) -> LoggerOrAdapterType:
    log = logging.getLogger("makora")
    if not debug:
        log.handlers.clear()
        log.setLevel(logging.CRITICAL + 10)
    else:
        fmt = RichFormatter()
        hnd = RichHandler()
        hnd.setLevel(logging.DEBUG)
        hnd.setFormatter(fmt)
        log.handlers.clear()
        log.addHandler(hnd)
        log.setLevel(logging.DEBUG)

    return BraceStyleAdapter(log)


def tear_down_logger(log: LoggerOrAdapterType | None) -> None:
    if log is None:
        return

    if isinstance(log, logging.LoggerAdapter):
        log = log.logger

    for hnd in log.handlers.copy():
        log.removeHandler(hnd)


_logger: LoggerOrAdapterType | None = None


def set_logger(
    log: LoggerOrAdapterType | None,
) -> LoggerOrAdapterType | None:
    global _logger
    old, _logger = _logger, log
    return old


@overload
def get_logger(default: EllipsisType = ...) -> LoggerOrAdapterType: ...


@overload
def get_logger(default: T) -> LoggerOrAdapterType | T: ...


def get_logger(default: T | EllipsisType = ...) -> LoggerOrAdapterType | T:
    if _logger is None:
        if isinstance(default, EllipsisType):
            raise RuntimeError("Logging not setup")
        return default

    return _logger


@contextmanager
def setup_logs() -> Generator[LoggerOrAdapterType, None, None]:
    log = get_logger(None)
    if log is not None:
        yield log
        return

    debug = bool(DEBUG.value == "1")
    log = configure_logger(debug)
    old = set_logger(log)
    try:
        yield log
    finally:
        set_logger(old)
        tear_down_logger(log)
