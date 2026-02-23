# storage/schema_storage.py
import json
import os
from core.models import Schema, FieldSchema, SourceConfig, FormatConfig

class SchemaStorage:
    """Сохранение и загрузка схем"""
    
    @staticmethod
    def save_schema(schema: Schema, filepath: str):
        """Сохранить схему в JSON файл"""
        data = {
            "name": schema.name,
            "fields": {}
        }
        
        for field_name, field in schema.fields.items():
            field_data = {
                "data_type": field.data_type,
                "formula": field.formula
            }
            
            # Добавляем источник, если есть
            if field.source:
                field_data["source"] = {
                    "type": field.source.type,
                    "selector": field.source.selector
                }
            else:
                field_data["source"] = None
            
            # Добавляем форматирование, если есть
            if field.format:
                field_data["format"] = {
                    "remove_text": field.format.remove_text,
                    "round_to": field.format.round_to,
                    "divide_by": field.format.divide_by,
                    "multiply_by": field.format.multiply_by,
                    "separator": field.format.separator
                }
            else:
                field_data["format"] = None
            
            data["fields"][field_name] = field_data
        
        # Создаём папку, если её нет
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        print(f"Схема сохранена: {filepath}")
    
    @staticmethod
    def load_schema(filepath: str) -> Schema:
        """Загрузить схему из JSON файла"""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        schema = Schema(name=data["name"])
        
        for field_name, field_data in data["fields"].items():
            # Восстанавливаем источник
            source = None
            if field_data.get("source"):
                source = SourceConfig(
                    type=field_data["source"]["type"],
                    selector=field_data["source"]["selector"]
                )
            
            # Восстанавливаем форматирование
            format_config = None
            if field_data.get("format"):
                fmt = field_data["format"]
                format_config = FormatConfig(
                    remove_text=fmt.get("remove_text"),
                    round_to=fmt.get("round_to"),
                    divide_by=fmt.get("divide_by"),
                    multiply_by=fmt.get("multiply_by"),
                    separator=fmt.get("separator")
                )
            
            # Создаём поле
            schema.fields[field_name] = FieldSchema(
                name=field_name,
                data_type=field_data["data_type"],
                source=source,
                format=format_config,
                formula=field_data.get("formula")
            )
        
        return schema
    
    @staticmethod
    def list_schemas(folder: str):
        """Показать все схемы в папке"""
        if not os.path.exists(folder):
            return []
        
        files = [f for f in os.listdir(folder) if f.endswith(".json")]
        return files
