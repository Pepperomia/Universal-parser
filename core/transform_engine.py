# core/transform_engine.py
import re
from typing import Any, Optional

class TransformEngine:
    """Мощный движок для форматирования и очистки данных"""
    
    def apply_format(self, value: Any, format_config) -> Any:
        """
        Применить форматирование к значению
        value - что форматируем
        format_config - настройки форматирования
        """
        if value is None:
            return None
        
        # Если значение - список, применяем форматирование к каждому элементу
        if isinstance(value, list):
            formatted_items = []
            for item in value:
                formatted = self._format_single_value(item, format_config)
                if formatted is not None:
                    formatted_items.append(formatted)
            
            # Соединяем список
            if format_config and format_config.separator:
                return format_config.separator.join(str(v) for v in formatted_items)
            else:
                return " | ".join(str(v) for v in formatted_items)
        
        # Одиночное значение
        return self._format_single_value(value, format_config)
    
    def _format_single_value(self, value: Any, format_config) -> Any:
        """Форматирование одного значения"""
        if value is None:
            return None
        
        # Преобразуем в строку для обработки
        str_value = str(value)
        
        # 1. Удаляем лишние пробелы в начале и конце
        str_value = str_value.strip()
        
        if format_config is None:
            return str_value
        
        # 2. Нормализация пробелов (один пробел между словами)
        if hasattr(format_config, 'normalize_whitespace') and format_config.normalize_whitespace:
            str_value = ' '.join(str_value.split())
        
        # 3. Удаляем ненужный текст
        if format_config.remove_text:
            for fragment in format_config.remove_text:
                str_value = str_value.replace(fragment, "")
            str_value = str_value.strip()
        
        # 4. Применяем регулярные выражения
        if format_config.regex_pattern:
            try:
                match = re.search(format_config.regex_pattern, str_value)
                if match:
                    if format_config.regex_group is not None:
                        str_value = match.group(format_config.regex_group)
                    else:
                        str_value = match.group(0)
            except Exception as e:
                print(f"⚠️ Ошибка regex: {e}")
        
        # 5. Пытаемся преобразовать в число
        if format_config.convert_to_number:
            num_value = self._extract_number(str_value)
            if num_value is not None:
                value = num_value
            else:
                value = str_value
        else:
            value = str_value
        
        # 6. Математические операции
        if isinstance(value, (int, float)):
            if format_config.multiply_by:
                value = value * format_config.multiply_by
            if format_config.divide_by:
                try:
                    value = value / format_config.divide_by
                except ZeroDivisionError:
                    value = None
            if format_config.round_to is not None:
                value = round(value, format_config.round_to)
        
        # 7. Обработка даты
        if format_config.date_format:
            value = self._format_date(value, format_config.date_format)
        
        return value
    
    def _extract_number(self, text: str) -> Optional[float]:
        """Извлечь число из текста"""
        # Ищем паттерн числа (целое или с десятичной точкой)
        match = re.search(r"(\d+\.?\d*)", text.replace(',', '.'))
        if match:
            num_str = match.group(1)
            try:
                if '.' in num_str:
                    return float(num_str)
                else:
                    return int(num_str)
            except:
                pass
        return None
    
    def _format_date(self, value: Any, date_format: str) -> str:
        """Форматирование даты (упрощённо)"""
        # Здесь можно добавить парсинг дат
        # Пока просто возвращаем как есть
        return str(value)
    
    def clean_html(self, text: str) -> str:
        """Удалить HTML теги из текста"""
        if not text:
            return text
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)
    
    def normalize_whitespace(self, text: str) -> str:
        """Нормализовать пробелы (один пробел между словами)"""
        if not text:
            return text
        return ' '.join(text.split())