#!/usr/bin/env python3
"""
Инструмент визуализации графа зависимостей пакетов
Этап 1: Минимальный прототип с конфигурацией
"""

import argparse
import sys
import os

class DependencyVisualizer:
    def __init__(self):
        self.config = {}
        
    def parse_arguments(self):
        """Парсинг аргументов командной строки"""
        parser = argparse.ArgumentParser(
            description='Инструмент визуализации графа зависимостей пакетов',
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        parser.add_argument(
            '--package',
            type=str,
            required=True,
            help='Имя анализируемого пакета'
        )
        
        parser.add_argument(
            '--source',
            type=str,
            required=True,
            help='URL-адрес репозитория или путь к файлу тестового репозитория'
        )
        
        parser.add_argument(
            '--test-mode',
            action='store_true',
            default=False,
            help='Режим работы с тестовым репозиторием'
        )
        
        parser.add_argument(
            '--output',
            type=str,
            default='dependency_graph.png',
            help='Имя сгенерированного файла с изображением графа'
        )
        
        parser.add_argument(
            '--ascii-tree',
            action='store_true',
            default=False,
            help='Режим вывода зависимостей в формате ASCII-дерева'
        )
        
        return parser.parse_args()
    
    def validate_arguments(self, args):
        """Валидация аргументов командной строки"""
        errors = []
        
        # Проверка имени пакета
        if not args.package or not args.package.strip():
            errors.append("Имя пакета не может быть пустым")
        
        # Проверка источника
        if not args.source or not args.source.strip():
            errors.append("Источник (URL или путь к файлу) не может быть пустым")
        
        # Проверка выходного файла
        if not args.output or not args.output.strip():
            errors.append("Имя выходного файла не может быть пустым")
        else:
            # Проверка расширения файла
            valid_extensions = ['.png', '.jpg', '.jpeg', '.svg', '.pdf']
            if not any(args.output.lower().endswith(ext) for ext in valid_extensions):
                errors.append(f"Неподдерживаемое расширение файла. Допустимые: {', '.join(valid_extensions)}")
        
        # Проверка существования файла в тестовом режиме
        if args.test_mode and not os.path.exists(args.source):
            errors.append(f"Тестовый файл не найден: {args.source}")
        
        return errors
    
    def print_configuration(self, args):
        """Вывод конфигурации в формате ключ-значение"""
        print("Конфигурация приложения:")
        print("=" * 40)
        print(f"Имя анализируемого пакета: {args.package}")
        print(f"Источник данных: {args.source}")
        print(f"Режим тестирования: {'Включен' if args.test_mode else 'Выключен'}")
        print(f"Выходной файл: {args.output}")
        print(f"Режим ASCII-дерева: {'Включен' if args.ascii_tree else 'Выключен'}")
        print("=" * 40)
    
    def run(self):
        """Основной метод запуска приложения"""
        try:
            # Парсинг аргументов
            args = self.parse_arguments()
            
            # Валидация аргументов
            errors = self.validate_arguments(args)
            if errors:
                print("Ошибки конфигурации:")
                for error in errors:
                    print(f"  - {error}")
                sys.exit(1)
            
            # Вывод конфигурации
            self.print_configuration(args)
            
            print("\nПриложение успешно запущено с указанной конфигурацией!")
            
        except Exception as e:
            print(f"Критическая ошибка: {e}")
            sys.exit(1)

if __name__ == "__main__":
    visualizer = DependencyVisualizer()
    visualizer.run()