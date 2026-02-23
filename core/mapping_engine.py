# core/mapping_engine.py
import pandas as pd
import os

class MappingEngine:
    """Движок для работы с Excel"""
    
    def create_excel(self, filepath, sheet_name, columns):
        """Создать новый Excel файл с указанными колонками"""
        df = pd.DataFrame(columns=columns)
        df.to_excel(filepath, sheet_name=sheet_name, index=False)
        print(f"Создан файл: {filepath}")
    
    def append_row(self, filepath, sheet_name, data_dict):
        """Добавить строку в Excel"""
        try:
            # Читаем существующий файл
            df = pd.read_excel(filepath, sheet_name=sheet_name)
            
            # Создаём новую строку в правильном порядке колонок
            new_row = {}
            for col in df.columns:
                new_row[col] = data_dict.get(col, "")
            
            # Добавляем строку
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            
            # Сохраняем
            with pd.ExcelWriter(filepath, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            print(f"Строка добавлена в {filepath}")
            
        except Exception as e:
            print(f"Ошибка добавления в Excel: {e}")
