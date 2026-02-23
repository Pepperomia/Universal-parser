# core/models.py
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List

@dataclass
class SourceConfig:
    """Настройки источника данных"""
    type: str  # css | xpath | json | regex | iframe
    selector: str
    attribute: Optional[str] = None  # для извлечения атрибутов (href, src)

@dataclass
class FormatConfig:
    """Настройки форматирования данных"""
    remove_text: Optional[List[str]] = None      # что удалить из текста
    round_to: Optional[int] = None               # округлить до скольки знаков
    divide_by: Optional[float] = None            # разделить на число
    multiply_by: Optional[float] = None          # умножить на число
    separator: Optional[str] = None              # разделитель для списков
    regex_pattern: Optional[str] = None          # регулярное выражение
    regex_group: Optional[int] = None            # группа регулярки (0 - всё)
    convert_to_number: bool = False              # преобразовать в число
    date_format: Optional[str] = None            # формат даты
    default_value: Optional[Any] = None          # значение по умолчанию
    normalize_whitespace: bool = False           # нормализовать пробелы

@dataclass
class FieldSchema:
    """Описание одного поля"""
    name: str
    data_type: str  # text | number | list | computed
    source: Optional[SourceConfig] = None
    format: Optional[FormatConfig] = None
    formula: Optional[str] = None                  # для вычисляемых полей
    required: bool = False                         # обязательное поле?
    multiple: bool = False                          # несколько значений?

@dataclass
class Schema:
    """Схема целиком"""
    name: str
    fields: Dict[str, FieldSchema] = field(default_factory=dict)
    site: Optional[str] = None                       # для какого сайта
    encoding: Optional[str] = None                    # кодировка
