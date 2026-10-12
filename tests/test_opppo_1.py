import io

import pytest

from opppo_1 import (
    CommandProcessor,
    Condition,
    DeviceContainer,
    DeviceFactory,
    Laptop,
    Smartphone,
    Tablet,
    parse_condition,
    parse_params,
)


@pytest.mark.parametrize(
    ("params", "expected_type", "expected_name"),
    [
        (
            {
                "type": "smartphone",
                "manufacturer": "Samsung",
                "year": "2022",
                "os": "Android 13",
                "memory": "256",
            },
            Smartphone,
            "smartphone",
        ),
        (
            {
                "type": "laptop",
                "manufacturer": "Apple",
                "year": "2021",
                "cpu": "M1",
                "ram": "16",
            },
            Laptop,
            "laptop",
        ),
        (
            {
                "type": "tablet",
                "manufacturer": "Apple",
                "year": "2012",
                "screen": "15.5",
                "battery": "1000",
            },
            Tablet,
            "tablet",
        ),
    ],
)
def test_factory_creates_each_device(params, expected_type, expected_name):
    device = DeviceFactory.create(params)

    assert isinstance(device, expected_type)
    assert device.type_name == expected_name
    assert device.manufacturer == params["manufacturer"]
    assert device.year == int(params["year"])


def test_factory_rejects_missing_type():
    with pytest.raises(ValueError, match="Не указан параметр 'type'"):
        DeviceFactory.create({"manufacturer": "Samsung", "year": "2022"})


def test_factory_rejects_missing_manufacturer():
    with pytest.raises(ValueError, match="Отсутствует обязательный параметр"):
        DeviceFactory.create({"type": "laptop", "year": "2021", "cpu": "M1", "ram": "16"})


def test_factory_rejects_unknown_device_type():
    with pytest.raises(ValueError, match="Неизвестный тип устройства"):
        DeviceFactory.create({"type": "watch", "manufacturer": "Apple", "year": "2024"})


def test_factory_rejects_invalid_year():
    with pytest.raises(ValueError):
        DeviceFactory.create(
            {
                "type": "laptop",
                "manufacturer": "Apple",
                "year": "not-a-year",
            }
        )


def test_factory_reports_missing_device_specific_parameter():
    with pytest.raises(KeyError):
        DeviceFactory.create(
            {"type": "smartphone", "manufacturer": "Samsung", "year": "2022"}
        )


def test_container_add_len_and_iteration():
    container = DeviceContainer()
    phone = Smartphone("Samsung", 2022, "Android 13", 256)
    laptop = Laptop("Apple", 2021, "M1", 16)

    container.add(phone)
    container.add(laptop)

    assert len(container) == 2
    assert list(container) == [phone, laptop]


def test_container_remove_if_removes_only_matching_devices():
    container = DeviceContainer()
    container.add(Smartphone("Samsung", 2022, "Android 13", 256))
    container.add(Laptop("Apple", 2021, "M1", 16))
    container.add(Tablet("Apple", 2012, 15.5, 1000))

    removed = container.remove_if(Condition("manufacturer", "=", "Apple").check)

    assert removed == 2
    assert len(container) == 1
    assert next(iter(container)).manufacturer == "Samsung"


def test_container_remove_if_returns_zero_when_nothing_matches():
    container = DeviceContainer()
    container.add(Smartphone("Samsung", 2022, "Android 13", 256))

    assert container.remove_if(Condition("year", "<", "2000").check) == 0
    assert len(container) == 1


def test_container_prints_empty_message(capsys):
    DeviceContainer().print_all()

    assert capsys.readouterr().out.strip() == "(контейнер пуст)"


def test_container_prints_devices(capsys):
    container = DeviceContainer()
    container.add(Smartphone("Samsung", 2022, "Android 13", 256))

    container.print_all()

    output = capsys.readouterr().out
    assert "Содержимое контейнера (1)" in output
    assert "[Smartphone] manufacturer=Samsung" in output


@pytest.mark.parametrize(
    ("operator", "value", "expected"),
    [
        ("=", "2022", True),
        ("!=", "2021", True),
        ("<", "2023", True),
        (">", "2021", True),
        ("<=", "2022", True),
        (">=", "2022", True),
        ("=", "2021", False),
    ],
)
def test_condition_numeric_comparison(operator, value, expected):
    device = Smartphone("Samsung", 2022, "Android 13", 256)

    assert Condition("year", operator, value).check(device) is expected


def test_condition_compares_strings_when_values_are_not_numeric():
    device = Smartphone("Samsung", 2022, "Android 13", 256)

    assert Condition("manufacturer", "=", "Samsung").check(device) is True
    assert Condition("manufacturer", "!=", "Apple").check(device) is True


def test_condition_returns_false_for_unknown_field():
    device = Smartphone("Samsung", 2022, "Android 13", 256)

    assert Condition("unknown", "=", "anything").check(device) is False


def test_condition_rejects_unknown_operator():
    device = Smartphone("Samsung", 2022, "Android 13", 256)

    with pytest.raises(ValueError, match="Неизвестный оператор"):
        Condition("year", "~", "2022").check(device)


def test_parse_params_parses_and_trims_values():
    result = parse_params(" type=laptop; year=2021 ; cpu=M1; ram=16 ")

    assert result == {
        "type": "laptop",
        "year": "2021",
        "cpu": "M1",
        "ram": "16",
    }


def test_parse_params_ignores_empty_pairs():
    assert parse_params("type=laptop;;year=2021;") == {
        "type": "laptop",
        "year": "2021",
    }


def test_parse_params_rejects_pair_without_equals():
    with pytest.raises(ValueError, match="Некорректная пара"):
        parse_params("type=laptop;year")


def test_parse_condition_parses_operator_and_spaces():
    condition = parse_condition(" year <= 2022 ")

    assert condition == Condition("year", "<=", "2022")


def test_parse_condition_rejects_missing_operator():
    with pytest.raises(ValueError, match="Некорректное условие"):
        parse_condition("year 2022")


def test_command_processor_add_and_print(capsys):
    processor = CommandProcessor()

    processor.process_line(
        "ADD type=smartphone;manufacturer=Samsung;year=2022;os=Android 13;memory=256"
    )
    processor.process_line("PRINT")

    output = capsys.readouterr().out
    assert "OK: добавлено" in output
    assert "Содержимое контейнера (1)" in output
    assert len(processor.container) == 1


def test_command_processor_remove(capsys):
    processor = CommandProcessor()
    processor.process_line(
        "ADD type=laptop;manufacturer=Apple;year=2021;cpu=M1;ram=16"
    )
    processor.process_line("REM year < 2022")

    output = capsys.readouterr().out
    assert "OK: удалено объектов: 1" in output
    assert len(processor.container) == 0


def test_command_processor_handles_invalid_add(capsys):
    processor = CommandProcessor()

    processor.process_line("ADD type=unknown;manufacturer=Test;year=2024")

    output = capsys.readouterr().out
    assert "Ошибка при обработке команды 'ADD'" in output
    assert len(processor.container) == 0


def test_command_processor_ignores_blank_lines_and_comments(capsys):
    processor = CommandProcessor()

    processor.process_line("")
    processor.process_line("   ")
    processor.process_line("# comment")

    assert capsys.readouterr().out == ""
    assert len(processor.container) == 0


def test_command_processor_reports_unknown_command(capsys):
    processor = CommandProcessor()

    processor.process_line("HELLO")

    assert "Неизвестная команда: HELLO" in capsys.readouterr().out


def test_command_processor_processes_stream(capsys):
    processor = CommandProcessor()
    stream = io.StringIO(
        "ADD type=tablet;manufacturer=Apple;year=2012;screen=15.5;battery=1000\n"
        "PRINT\n"
    )

    processor.process_stream(stream)

    output = capsys.readouterr().out
    assert "OK: добавлено" in output
    assert "Содержимое контейнера (1)" in output
    assert len(processor.container) == 1


def test_command_processor_processes_file(tmp_path, capsys):
    input_file = tmp_path / "commands.txt"
    input_file.write_text(
        "ADD type=laptop;manufacturer=Apple;year=2021;cpu=M1;ram=16\nPRINT\n",
        encoding="utf-8",
    )
    processor = CommandProcessor()

    processor.process_file(str(input_file))

    output = capsys.readouterr().out
    assert "OK: добавлено" in output
    assert "Содержимое контейнера (1)" in output
    assert len(processor.container) == 1
