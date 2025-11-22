#!/usr/bin/env python3
"""
Инструмент визуализации графа зависимостей пакетов
Этап 3: Основные операции
"""

import argparse
import sys
import os
import json
import urllib.request
import urllib.error
from collections import deque, defaultdict

class DependencyVisualizer:
    def __init__(self):
        self.config = {}
        self.dependency_graph = defaultdict(dict)
        self.visited = set()
        self.cycle_detected = False
        
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
        
        if not args.package or not args.package.strip():
            errors.append("Имя пакета не может быть пустым")
        
        if not args.source or not args.source.strip():
            errors.append("Источник (URL или путь к файлу) не может быть пустым")
        
        if not args.output or not args.output.strip():
            errors.append("Имя выходного файла не может быть пустым")
        
        if args.test_mode and not os.path.exists(args.source):
            errors.append(f"Тестовый файл не найден: {args.source}")
        
        return errors
    
    def get_package_info_from_url(self, package_name):
        """Получение информации о пакете из npm реестра"""
        try:
            npm_registry_url = f"https://registry.npmjs.org/{package_name}"
            
            with urllib.request.urlopen(npm_registry_url) as response:
                data = json.loads(response.read().decode())
            
            if 'dist-tags' in data and 'latest' in data['dist-tags']:
                latest_version = data['dist-tags']['latest']
            else:
                latest_version = list(data.get('versions', {}).keys())[0]
            
            version_data = data['versions'][latest_version]
            dependencies = version_data.get('dependencies', {})
            
            return {
                'name': package_name,
                'version': latest_version,
                'dependencies': dependencies
            }
            
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise Exception(f"Пакет '{package_name}' не найден в npm реестре")
            else:
                raise Exception(f"Ошибка HTTP при запросе пакета: {e}")
        except Exception as e:
            raise Exception(f"Ошибка при получении информации о пакете '{package_name}': {e}")
    
    def get_package_info_from_file(self, package_name, file_path):
        """Получение информации о пакете из тестового файла"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Поддержка формата с пакетами в виде больших латинских букв
            if package_name in data:
                package_info = data[package_name]
            else:
                # Попробовать найти пакет в другом формате
                raise Exception(f"Пакет '{package_name}' не найден в тестовом файле")
            
            return {
                'name': package_name,
                'version': package_info.get('version', '1.0.0'),
                'dependencies': package_info.get('dependencies', {})
            }
            
        except Exception as e:
            raise Exception(f"Ошибка при чтении тестового файла: {e}")
    
    def build_dependency_graph_bfs_recursive(self, queue, args, max_depth=10):
        """Построение графа зависимостей с помощью BFS с рекурсией"""
        
        if not queue:
            return
        
        
        current_package, depth = queue.popleft()
        
        if depth > max_depth:
            print(f"Предупреждение: достигнута максимальная глубина {max_depth} для пакета {current_package}")
            
            self.build_dependency_graph_bfs_recursive(queue, args, max_depth)
            return
        
        try:
            
            if args.test_mode:
                package_info = self.get_package_info_from_file(current_package, args.source)
            else:
                package_info = self.get_package_info_from_url(current_package)
            
            dependencies = package_info.get('dependencies', {})
            
            
            self.dependency_graph[current_package] = dependencies
            
            
            for dep_name in dependencies.keys():
                
                if dep_name in self.dependency_graph and current_package in self.dependency_graph.get(dep_name, {}):
                    print(f"Обнаружена циклическая зависимость: {current_package} <-> {dep_name}")
                    self.cycle_detected = True
                    continue
                
                
                if dep_name not in self.visited:
                    self.visited.add(dep_name)
                    queue.append((dep_name, depth + 1))
                    
        except Exception as e:
            print(f"Ошибка при обработке пакета {current_package}: {e}")
        
        
        self.build_dependency_graph_bfs_recursive(queue, args, max_depth)
    
    def build_dependency_graph_bfs(self, start_package, args, max_depth=10):
        """Обертка для запуска BFS с рекурсией"""
        queue = deque([(start_package, 0)])
        self.visited.add(start_package)
        self.build_dependency_graph_bfs_recursive(queue, args, max_depth)
    
    def print_ascii_tree(self, package, graph, prefix="", is_last=True):
        """Вывод графа в формате ASCII-дерева"""
        connectors = "└── " if is_last else "├── "
        print(prefix + connectors + package)
        
        dependencies = list(graph.get(package, {}).keys())
        new_prefix = prefix + ("    " if is_last else "│   ")
        
        for i, dep in enumerate(dependencies):
            is_last_dep = i == len(dependencies) - 1
            if dep in graph:
                self.print_ascii_tree(dep, graph, new_prefix, is_last_dep)
            else:
                connector = "└── " if is_last_dep else "├── "
                print(new_prefix + connector + dep + " (не раскрыто)")
    
    def print_graph_info(self):
        """Вывод информации о построенном графе"""
        print(f"\nИнформация о графе зависимостей:")
        print("-" * 40)
        print(f"Всего пакетов: {len(self.dependency_graph)}")
        print(f"Обнаружены циклические зависимости: {'Да' if self.cycle_detected else 'Нет'}")
        
        total_dependencies = sum(len(deps) for deps in self.dependency_graph.values())
        print(f"Всего зависимостей: {total_dependencies}")
        print("-" * 40)
        
        print("\nДетали графа:")
        for package, dependencies in self.dependency_graph.items():
            print(f"\n{package}:")
            for dep, version in dependencies.items():
                status = "✓" if dep in self.dependency_graph else "✗"
                print(f"  {status} {dep}: {version}")
    
    def demonstrate_test_cases(self):
        """Демонстрация различных случаев работы с тестовым репозиторием"""
        test_cases = [
            {
                "name": "Простая цепочка зависимостей",
                "file": "test_simple.json",
                "package": "A"
            },
            {
                "name": "Циклические зависимости", 
                "file": "test_cycle.json",
                "package": "A"
            },
            {
                "name": "Множественные зависимости",
                "file": "test_complex.json", 
                "package": "A"
            }
        ]
        
        print("\nДемонстрация работы с тестовыми случаями:")
        print("=" * 50)
        
        for test_case in test_cases:
            print(f"\nТестовый случай: {test_case['name']}")
            print(f"Файл: {test_case['file']}, Пакет: {test_case['package']}")
            
            if os.path.exists(test_case['file']):
                # Сбрасываем состояние для нового теста
                self.dependency_graph.clear()
                self.visited.clear()
                self.cycle_detected = False
                
                try:
                    self.build_dependency_graph_bfs(
                        test_case['package'], 
                        argparse.Namespace(
                            test_mode=True,
                            source=test_case['file']
                        )
                    )
                    self.print_graph_info()
                except Exception as e:
                    print(f"Ошибка: {e}")
            else:
                print(f"Файл {test_case['file']} не найден")
    
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
            
            print("Конфигурация приложения:")
            print("=" * 40)
            print(f"Имя анализируемого пакета: {args.package}")
            print(f"Источник данных: {args.source}")
            print(f"Режим тестирования: {'Включен' if args.test_mode else 'Выключен'}")
            print(f"Выходной файл: {args.output}")
            print(f"Режим ASCII-дерева: {'Включен' if args.ascii_tree else 'Выключен'}")
            print("=" * 40)
            
            # Построение графа зависимостей
            print(f"\nПостроение графа зависимостей для пакета '{args.package}'...")
            self.build_dependency_graph_bfs(args.package, args)
            
            # Вывод результатов
            self.print_graph_info()
            
            # Вывод ASCII-дерева если запрошено
            if args.ascii_tree:
                print(f"\nASCII-дерево зависимостей для '{args.package}':")
                print("=" * 50)
                self.print_ascii_tree(args.package, self.dependency_graph)
            
            # Демонстрация тестовых случаев если в тестовом режиме
            if args.test_mode:
                self.demonstrate_test_cases()
            
            print("\nЭтап 3 завершен успешно!")
            
        except Exception as e:
            print(f"Ошибка: {e}")
            sys.exit(1)

if __name__ == "__main__":
    visualizer = DependencyVisualizer()
    visualizer.run()