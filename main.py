#!/usr/bin/env python3
"""
Инструмент визуализации графа зависимостей пакетов
Этап 4: Дополнительные операции (BFS с рекурсией)
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
        self.reverse_dependency_graph = defaultdict(list)
        self.visited = set()
        self.cycle_detected = False
        self.cycle_paths = []
        
    def parse_arguments(self):
        """Парсинг аргументов командной строки"""
        parser = argparse.ArgumentParser(
            description='Инструмент визуализации графа зависимостей пакетов - Этап 4',
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
            '--reverse-deps',
            action='store_true',
            default=False,
            help='Показать обратные зависимости (пакеты, зависящие от данного)'
        )
        
        parser.add_argument(
            '--reverse-for',
            type=str,
            help='Имя пакета для показа обратных зависимостей'
        )
        
        parser.add_argument(
            '--depth',
            type=int,
            default=5,
            help='Максимальная глубина рекурсии'
        )
        
        return parser.parse_args()
    
    def validate_arguments(self, args):
        """Валидация аргументов командной строки"""
        errors = []
        
        if not args.package or not args.package.strip():
            errors.append("Имя пакета не может быть пустым")
        
        if not args.source or not args.source.strip():
            errors.append("Источник (URL или путь к файлу) не может быть пустым")
        
        if args.test_mode and not os.path.exists(args.source):
            errors.append(f"Тестовый файл не найден: {args.source}")
        
        if args.depth <= 0:
            errors.append("Глубина должна быть положительным числом")
        
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
                # Берем первую доступную версию
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
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if package_name in data:
                package_info = data[package_name]
            else:
                # Пробуем найти пакет в другом формате
                raise Exception(f"Пакет '{package_name}' не найден в тестовом файле")
            
            return {
                'name': package_name,
                'version': package_info.get('version', '1.0.0'),
                'dependencies': package_info.get('dependencies', {})
            }
            
        except Exception as e:
            raise Exception(f"Ошибка при чтении тестового файла: {e}")
    
    def build_complete_dependency_graph(self, args):
        """Построение полного графа зависимостей из тестового файла"""
        if not args.test_mode:
            return
            
        try:
            with open(args.source, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Строим граф для всех пакетов в файле
            for package_name in data.keys():
                if package_name not in self.dependency_graph:
                    package_info = self.get_package_info_from_file(package_name, args.source)
                    dependencies = package_info.get('dependencies', {})
                    self.dependency_graph[package_name] = dependencies
                    
                    # Строим обратный граф
                    for dep_name in dependencies.keys():
                        self.reverse_dependency_graph[dep_name].append(package_name)
                        
        except Exception as e:
            print(f"Ошибка при построении полного графа: {e}")
    
    def build_dependency_graph_bfs_recursive(self, queue, args, max_depth=10):
        """Построение графа зависимостей с помощью BFS с рекурсией"""
        # Базовый случай рекурсии - очередь пуста
        if not queue:
            return
        
        # Берем пакет из начала очереди
        current_package, depth = queue.popleft()
        
        if depth > max_depth:
            print(f"Предупреждение: достигнута максимальная глубина {max_depth} для пакета {current_package}")
            # Продолжаем рекурсию с оставшимися элементами очереди
            self.build_dependency_graph_bfs_recursive(queue, args, max_depth)
            return
        
        try:
            # Получение информации о пакете
            if args.test_mode:
                package_info = self.get_package_info_from_file(current_package, args.source)
            else:
                package_info = self.get_package_info_from_url(current_package)
            
            dependencies = package_info.get('dependencies', {})
            
            # Сохраняем зависимости в графе
            self.dependency_graph[current_package] = dependencies
            
            # Строим обратный граф зависимостей
            for dep_name in dependencies.keys():
                self.reverse_dependency_graph[dep_name].append(current_package)
            
            # Обрабатываем зависимости через for, добавляем в очередь
            for dep_name in dependencies.keys():
                # Проверка на циклические зависимости
                if dep_name in self.dependency_graph and current_package in self.dependency_graph.get(dep_name, {}):
                    print(f"Обнаружена циклическая зависимость: {current_package} <-> {dep_name}")
                    self.cycle_detected = True
                    self.cycle_paths.append([current_package, dep_name])
                    continue
                
                # Добавляем в очередь только если еще не посещали
                if dep_name not in self.visited:
                    self.visited.add(dep_name)
                    queue.append((dep_name, depth + 1))
                    
        except Exception as e:
            print(f"Ошибка при обработке пакета {current_package}: {e}")
            # ВАЖНО: Даже при ошибке добавляем пакет в граф (без зависимостей)
            self.dependency_graph[current_package] = {}
        
        # Рекурсивный вызов для обработки следующего пакета в очереди
        self.build_dependency_graph_bfs_recursive(queue, args, max_depth)
    
    def build_dependency_graph_bfs(self, start_package, args):
        """Обертка для запуска BFS с рекурсией"""
        queue = deque([(start_package, 0)])
        self.visited.add(start_package)
        self.build_dependency_graph_bfs_recursive(queue, args, args.depth)
    
    def find_reverse_dependencies_bfs_recursive(self, queue, visited, reverse_deps):
        """Поиск обратных зависимостей с помощью BFS с рекурсией"""
        # Базовый случай рекурсии - очередь пуста
        if not queue:
            return
        
        # Берем пакет из начала очереди
        current_package = queue.popleft()
        
        # Добавляем в результат
        if current_package not in reverse_deps:
            reverse_deps.add(current_package)
        
        # Обрабатываем обратные зависимости через for
        for dependent in self.reverse_dependency_graph.get(current_package, []):
            if dependent not in visited:
                visited.add(dependent)
                queue.append(dependent)
        
        # Рекурсивный вызов для обработки следующего пакета в очереди
        self.find_reverse_dependencies_bfs_recursive(queue, visited, reverse_deps)
    
    def find_reverse_dependencies(self, package_name):
        """Поиск всех пакетов, которые зависят от заданного пакета с помощью BFS с рекурсией"""
        reverse_deps = set()
        visited = set([package_name])
        queue = deque([package_name])
        
        self.find_reverse_dependencies_bfs_recursive(queue, visited, reverse_deps)
        return reverse_deps
    
    def build_reverse_dependency_tree_bfs_recursive(self, queue, visited, tree):
        """Построение дерева обратных зависимостей с помощью BFS с рекурсией"""
        # Базовый случай рекурсии - очередь пуста
        if not queue:
            return
        
        # Берем пакет из начала очереди
        current_package = queue.popleft()
        
        # Обрабатываем обратные зависимости через for
        for dependent in self.reverse_dependency_graph.get(current_package, []):
            if dependent not in visited:
                visited.add(dependent)
                tree[current_package].append(dependent)
                queue.append(dependent)
        
        # Рекурсивный вызов для обработки следующего пакета в очереди
        self.build_reverse_dependency_tree_bfs_recursive(queue, visited, tree)
    
    def build_reverse_dependency_tree(self, package_name):
        """Построение дерева обратных зависимостей с помощью BFS с рекурсией"""
        tree = defaultdict(list)
        visited = set([package_name])
        queue = deque([package_name])
        
        self.build_reverse_dependency_tree_bfs_recursive(queue, visited, tree)
        return tree
    
    def find_tree_roots(self, tree, all_nodes):
        """Нахождение корневых узлов дерева"""
        # Все узлы, которые являются зависимыми
        all_dependents = set()
        for deps in tree.values():
            all_dependents.update(deps)
        
        # Корни - узлы, которые никто не зависит от них в этом дереве
        roots = [node for node in all_nodes if node not in all_dependents]
        return roots
    
    def print_reverse_dependencies(self, package_name):
        """Вывод обратных зависимостей в виде дерева"""
        reverse_deps = self.find_reverse_dependencies(package_name)
        
        if not reverse_deps:
            print(f"\nНет пакетов, зависящих от '{package_name}'")
            return
        
        print(f"\nПакеты, зависящие от '{package_name}':")
        print("=" * 50)
        
        # Строим дерево обратных зависимостей
        tree = self.build_reverse_dependency_tree(package_name)
        
        # Собираем все узлы дерева
        all_nodes = set([package_name])
        for deps in tree.values():
            all_nodes.update(deps)
        
        roots = self.find_tree_roots(tree, all_nodes)
        
        def print_tree_bfs_recursive(queue, prefix="", visited=None):
            """Вывод дерева с помощью BFS с рекурсией"""
            if not queue:
                return
                
            if visited is None:
                visited = set()
            
            current_level_size = len(queue)
            next_level_queue = deque()
            
            for i, node in enumerate(queue):
                if node in visited:
                    connector = "└── " if i == current_level_size - 1 else "├── "
                    print(prefix + connector + node + " (циклическая ссылка)")
                    continue
                    
                visited.add(node)
                
                connector = "└── " if i == current_level_size - 1 else "├── "
                node_display = node
                if node == package_name:
                    node_display += " (целевой пакет)"
                print(prefix + connector + node_display)
                
                # Добавляем детей в очередь следующего уровня
                children = sorted(tree.get(node, []))
                for child in children:
                    next_level_queue.append(child)
            
            # Рекурсивный вызов для следующего уровня
            if next_level_queue:
                new_prefix = prefix + "    "
                print_tree_bfs_recursive(next_level_queue, new_prefix, visited)
        
        # Выводим дерево начиная с корней
        if roots:
            print_tree_bfs_recursive(deque(roots))
        else:
            # Если корней нет (циклическая зависимость), начинаем с целевого пакета
            print_tree_bfs_recursive(deque([package_name]))
    
    def demonstrate_reverse_deps_cases(self):
        """Демонстрация различных случаев обратных зависимостей"""
        test_cases = [
            {
                "name": "Простая цепочка обратных зависимостей",
                "file": "test_simple.json",
                "target_package": "C"
            },
            {
                "name": "Множественные обратные зависимости",
                "file": "test_complex.json", 
                "target_package": "D"
            },
            {
                "name": "Циклические зависимости с обратными связями",
                "file": "test_cycle.json",
                "target_package": "A"
            }
        ]
        
        print("\nДемонстрация обратных зависимостей для тестовых случаев:")
        print("=" * 60)
        
        for test_case in test_cases:
            print(f"\nТестовый случай: {test_case['name']}")
            print(f"Файл: {test_case['file']}, Целевой пакет: {test_case['target_package']}")
            
            if os.path.exists(test_case['file']):
                # Сбрасываем состояние для нового теста
                self.dependency_graph.clear()
                self.reverse_dependency_graph.clear()
                self.visited.clear()
                self.cycle_detected = False
                self.cycle_paths.clear()
                
                try:
                    # Строим полный граф из тестового файла
                    args = argparse.Namespace(
                        test_mode=True,
                        source=test_case['file'],
                        depth=5
                    )
                    self.build_complete_dependency_graph(args)
                    
                    # Выводим обратные зависимости
                    self.print_reverse_dependencies(test_case['target_package'])
                    
                    # Показываем информацию о циклах если есть
                    if self.cycle_paths:
                        print(f"\nОбнаруженные циклические зависимости:")
                        for cycle in self.cycle_paths:
                            print(f"  {' -> '.join(cycle)}")
                    
                except Exception as e:
                    print(f"Ошибка: {e}")
            else:
                print(f"Файл {test_case['file']} не найден")
    
    def print_graph_statistics(self):
        """Вывод статистики графа"""
        print(f"\nСтатистика графа зависимостей:")
        print("-" * 40)
        print(f"Всего пакетов: {len(self.dependency_graph)}")
        print(f"Всего зависимостей: {sum(len(deps) for deps in self.dependency_graph.values())}")
        print(f"Обнаружены циклические зависимости: {'Да' if self.cycle_detected else 'Нет'}")
        print(f"Размер графа обратных зависимостей: {len(self.reverse_dependency_graph)}")
        
        # Статистика по обратным зависимостям
        if self.reverse_dependency_graph:
            reverse_deps_count = {pkg: len(deps) for pkg, deps in self.reverse_dependency_graph.items()}
            if reverse_deps_count:
                max_reverse_deps = max(reverse_deps_count.values())
                popular_packages = [pkg for pkg, count in reverse_deps_count.items() 
                                  if count == max_reverse_deps]
                
                print(f"Наиболее популярный пакет: {popular_packages[0]} ({max_reverse_deps} зависимостей)")
        
        # Информация о циклах
        if self.cycle_paths:
            print(f"Обнаружено циклических путей: {len(self.cycle_paths)}")
            for i, cycle in enumerate(self.cycle_paths[:3]):  # Показываем первые 3 цикла
                print(f"  Цикл {i+1}: {' -> '.join(cycle)}")
        
        # ВЫВОД ЗАВИСИМОСТЕЙ
        print(f"\nПервые 15 пакетов и их зависимости:")
        print("-" * 50)
        count = 0
        for package, dependencies in sorted(self.dependency_graph.items()):
            if count >= 15:
                break
            if dependencies:
                print(f"\n{package}:")
                for dep, version in sorted(dependencies.items()):
                    print(f"  → {dep}: {version}")
            else:
                print(f"\n{package}: (нет зависимостей)")
            count += 1
    
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
            
            print("Конфигурация приложения (Этап 4 - BFS с рекурсией):")
            print("=" * 50)
            print(f"Имя анализируемого пакета: {args.package}")
            print(f"Источник данных: {args.source}")
            print(f"Режим тестирования: {'Включен' if args.test_mode else 'Выключен'}")
            print(f"Режим обратных зависимостей: {'Включен' if args.reverse_deps else 'Выключен'}")
            if args.reverse_for:
                print(f"Поиск обратных зависимостей для: {args.reverse_for}")
            print(f"Максимальная глубина: {args.depth}")
            print("=" * 50)
            
            # Построение графа зависимостей
            print(f"\nПостроение графа зависимостей для пакета '{args.package}'...")
            
            if args.test_mode:
                # В тестовом режиме строим полный граф из файла
                self.build_complete_dependency_graph(args)
            else:
                # В продакшн режиме строим граф BFS с рекурсией
                self.build_dependency_graph_bfs(args.package, args)
            
            # Вывод статистики
            self.print_graph_statistics()
            
            # Обработка обратных зависимостей
            if args.reverse_deps or args.reverse_for:
                target_package = args.reverse_for if args.reverse_for else args.package
                print(f"\nАнализ обратных зависимостей для пакета '{target_package}':")
                self.print_reverse_dependencies(target_package)
            
            # Демонстрация тестовых случаев если в тестовом режиме
            if args.test_mode:
                self.demonstrate_reverse_deps_cases()
            
            print("\nЭтап 4 завершен успешно!")
            
        except Exception as e:
            print(f"Ошибка: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == "__main__":
    visualizer = DependencyVisualizer()
    visualizer.run()