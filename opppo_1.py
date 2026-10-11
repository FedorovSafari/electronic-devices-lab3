from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Any, ClassVar


#Базовый класс
class ElectronicDevice(ABC):
    def __init__(self, manufacturer: str, year: int):
        self.manufacturer = manufacturer
        self.year = year

    def get_field(self, name: str) -> str:
        if name == "manufacturer":
            return self.manufacturer
        if name == "year":
            return str(self.year)
        return ""

    @property
    @abstractmethod
    def type_name(self) -> str: ...
    @abstractmethod
    def __str__(self) -> str: ...


#Наследники
class Smartphone(ElectronicDevice):
    def __init__(self, manufacturer: str, year: int, os: str, memory: int):
        super().__init__(manufacturer, year)
        self.os = os
        self.memory = memory

    @property
    def type_name(self) -> str:
        return "smartphone"

    def get_field(self, name: str) -> str:
        if name == "os":
            return self.os
        if name == "memory":
            return str(self.memory)
        return super().get_field(name)

    def __str__(self) -> str:
        return (f"[Smartphone] manufacturer={self.manufacturer}, "
                f"year={self.year}, os={self.os}, memory={self.memory}GB")


class Laptop(ElectronicDevice):
    def __init__(self, manufacturer: str, year: int, cpu: str, ram: int):
        super().__init__(manufacturer, year)
        self.cpu = cpu
        self.ram = ram

    @property
    def type_name(self) -> str:
        return "laptop"

    def get_field(self, name: str) -> str:
        if name == "cpu":
            return self.cpu
        if name == "ram":
            return str(self.ram)
        return super().get_field(name)

    def __str__(self) -> str:
        return (f"[Laptop] manufacturer={self.manufacturer}, "
                f"year={self.year}, cpu={self.cpu}, ram={self.ram}GB")


class Tablet(ElectronicDevice):
    def __init__(self, manufacturer: str, year: int, screen: float, battery: int):
        super().__init__(manufacturer, year)
        self.screen = screen
        self.battery = battery

    @property
    def type_name(self) -> str:
        return "tablet"

    def get_field(self, name: str) -> str:
        if name == "screen":
            return str(self.screen)
        if name == "battery":
            return str(self.battery)
        return super().get_field(name)

    def __str__(self) -> str:
        return (f"[Tablet] manufacturer={self.manufacturer}, "
                f"year={self.year}, screen={self.screen}\", "
                f"battery={self.battery}mAh")


#Фабрика
class DeviceFactory:

    @staticmethod
    def create(params: dict[str, str]) -> ElectronicDevice:
        dtype = params.get("type")
        if not dtype:
            raise ValueError("Не указан параметр 'type'")

        try:
            manufacturer = params["manufacturer"]
            year = int(params["year"])
        except KeyError as e:
            raise ValueError(f"Отсутствует обязательный параметр: {e}") from e

        if dtype == "smartphone":
            return Smartphone(manufacturer, year,
                              params["os"], int(params["memory"]))
        if dtype == "laptop":
            return Laptop(manufacturer, year,
                          params["cpu"], int(params["ram"]))
        if dtype == "tablet":
            return Tablet(manufacturer, year,
                          float(params["screen"]), int(params["battery"]))

        raise ValueError(f"Неизвестный тип устройства: {dtype}")


#Контейнер
class DeviceContainer:

    def __init__(self):
        self._devices: list[ElectronicDevice] = []

    def add(self, device: ElectronicDevice) -> None:
        self._devices.append(device)

    def remove_if(self, predicate: Callable[[ElectronicDevice], bool]) -> int:
        before = len(self._devices)
        self._devices = [d for d in self._devices if not predicate(d)]
        return before - len(self._devices)

    def print_all(self) -> None:
        if not self._devices:
            print("(контейнер пуст)")
            return
        print(f"=== Содержимое контейнера ({len(self._devices)}) ===")
        for d in self._devices:
            print(f"  {d}")

    def __len__(self) -> int:
        return len(self._devices)

    def __iter__(self) -> Iterator[ElectronicDevice]:
        return iter(self._devices)


#Условие
@dataclass
class Condition:
    field: str
    op: str
    value: str

    _OPS: ClassVar[dict[str, Callable[[Any, Any], bool]]] = {
        "=": lambda a, b: a == b,
        "!=": lambda a, b: a != b,
        "<": lambda a, b: a < b,
        ">": lambda a, b: a > b,
        "<=": lambda a, b: a <= b,
        ">=": lambda a, b: a >= b,
    }

    def check(self, device: ElectronicDevice) -> bool:
        actual = device.get_field(self.field)  # ← полиморфный вызов
        if actual == "":
            return False

        cmp = self._OPS.get(self.op)
        if cmp is None:
            raise ValueError(f"Неизвестный оператор: {self.op}")

        # Пытаемся сравнивать как числа, иначе как строки
        try:
            return cmp(float(actual), float(self.value))
        except ValueError:
            return cmp(actual, self.value)


#Парсер
def parse_params(raw: str) -> dict[str, str]:
    """'type=laptop; year=2021; cpu=M1' → {'type': 'laptop', ...}"""
    params: dict[str, str] = {}
    for pair in raw.split(";"):
        pair = pair.strip()
        if not pair:
            continue
        if "=" not in pair:
            raise ValueError(f"Некорректная пара: '{pair}'")
        key, _, value = pair.partition("=")
        params[key.strip()] = value.strip()
    return params


def parse_condition(raw: str) -> Condition:
    """'year < 2022' → Condition('year', '<', '2022')"""
    raw = raw.strip()
    for op in ("<=", ">=", "!=", "=", "<", ">"):
        if op in raw:
            left, _, right = raw.partition(op)
            return Condition(left.strip(), op, right.strip())
    raise ValueError(f"Некорректное условие: '{raw}'")


#Обработчик команд
class CommandProcessor:
    def __init__(self):
        self.container = DeviceContainer()

    def process_line(self, line: str) -> None:
        line = line.strip()
        if not line or line.startswith("#"):
            return

        cmd, _, args = line.partition(" ")
        cmd = cmd.upper()
        args = args.strip()

        try:
            if cmd == "ADD":
                params = parse_params(args)
                device = DeviceFactory.create(params)
                self.container.add(device)
                print("OK: добавлено")

            elif cmd == "REM":
                condition = parse_condition(args)
                removed = self.container.remove_if(condition.check)
                print(f"OK: удалено объектов: {removed}")

            elif cmd == "PRINT":
                self.container.print_all()

            else:
                print(f"Неизвестная команда: {cmd}")

        except (ValueError, KeyError) as e:
            print(f"Ошибка при обработке команды '{cmd}': {e}")

    def process_file(self, path: str) -> None:
        with open(path, encoding="utf-8") as f:
            for line in f:
                self.process_line(line)

    def process_stream(self, stream) -> None:
        for line in stream:
            self.process_line(line)


#main
def main() -> None:
    processor = CommandProcessor()
    if len(sys.argv) > 1:
        processor.process_file(sys.argv[1])
    else:
        processor.process_stream(sys.stdin)


if __name__ == "__main__":
    main()