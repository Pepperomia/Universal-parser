# core/schema_engine.py
from core.transform_engine import TransformEngine

class SchemaEngine:
    """Движок для применения схемы к странице"""
    
    def __init__(self):
        self.transformer = TransformEngine()
    
    def apply_schema(self, soup, schema, parser_engine):
        """
        Применить схему к загруженной странице
        soup - объект BeautifulSoup
        schema - объект Schema
        parser_engine - объект ParserEngine
        """
        result = {}
        errors = []
        
        # Пробуем извлечь JSON из страницы (если есть)
        json_data = parser_engine.extract_json_next_data(soup)
        json_ld = parser_engine.extract_json_ld(soup)
        
        for field_name, field in schema.fields.items():
            try:
                # Вычисляемые поля
                if field.data_type == "computed":
                    result[field_name] = self._evaluate_formula(field.formula, result)
                    continue
                
                # Обычные поля
                raw_value = None
                
                if field.source is None:
                    if field.required:
                        errors.append(f"Поле {field_name}: не указан источник")
                    continue
                
                # Выбираем источник данных
                if field.source.type == "css":
                    raw_value = parser_engine.extract_css(
                        soup,
                        field.source.selector,
                        field.source.attribute
                    )
                    
                elif field.source.type == "xpath":
                    raw_value = parser_engine.extract_xpath(
                        soup,
                        field.source.selector,
                        field.source.attribute
                    )
                    
                elif field.source.type == "json" and json_data:
                    raw_value = parser_engine.extract_json_path(
                        json_data,
                        field.source.selector
                    )
                    
                elif field.source.type == "json-ld" and json_ld:
                    # Простейший доступ к JSON-LD
                    if field.source.selector in json_ld[0]:
                        raw_value = json_ld[0][field.source.selector]
                
                # Применяем форматирование
                formatted = self.transformer.apply_format(
                    raw_value,
                    field.format
                )
                
                # Если значение пустое, используем значение по умолчанию
                if not formatted and field.format and field.format.default_value is not None:
                    formatted = field.format.default_value
                
                # Проверяем обязательные поля
                if field.required and not formatted:
                    errors.append(f"Поле {field_name}: обязательное поле не заполнено")
                
                result[field_name] = formatted
                
            except Exception as e:
                errors.append(f"Поле {field_name}: ошибка - {e}")
                result[field_name] = None
        
        # Добавляем информацию об ошибках
        if errors:
            result['_errors'] = errors
        
        return result
    
    def _evaluate_formula(self, formula, data):
        """Вычислить значение по формуле (безопасная версия)"""
        if not formula:
            return None
        
        try:
            # Создаём безопасное окружение
            safe_dict = {
                'int': int,
                'float': float,
                'str': str,
                'len': len,
                'sum': sum,
                'round': round,
                'abs': abs,
                'max': max,
                'min': min
            }
            # Добавляем данные
            safe_dict.update(data)
            
            return eval(formula, {"__builtins__": {}}, safe_dict)
        except Exception as e:
            print(f"⚠️ Ошибка вычисления формулы: {e}")
            return None
