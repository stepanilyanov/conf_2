#!/usr/bin/env python3
"""
Инструмент визуализации графа зависимостей пакетов
Этап 5: Визуализация (BFS с рекурсией)
"""

import argparse
import sys
import os
import json
import urllib.request
import urllib.error
import subprocess
import tempfile
from collections import deque, defaultdict
import webbrowser

class DependencyVisualizer:
    def __init__(self):
        self.dependency_graph = defaultdict(dict)
        self.visited = set()
        
    def parse_arguments(self):
        """Парсинг аргументов командной строки"""
        parser = argparse.ArgumentParser(
            description='Инструмент визуализации графа зависимостей пакетов - Этап 5',
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
            help='URL npm реестра или путь к тестовому файлу'
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
            default='dependency_graph.svg',
            help='Имя выходного файла'
        )
        
        parser.add_argument(
            '--ascii-tree',
            action='store_true',
            default=False,
            help='Вывод зависимостей в формате ASCII-дерева'
        )
        
        parser.add_argument(
            '--format',
            type=str,
            choices=['svg', 'png', 'pdf'],
            default='svg',
            help='Формат выходного файла'
        )
        
        parser.add_argument(
            '--compare-npm',
            action='store_true',
            default=False,
            help='Сравнить с выводом npm'
        )
        
        parser.add_argument(
            '--depth',
            type=int,
            default=3,
            help='Глубина анализа зависимостей'
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
    
    def get_package_info_from_npm(self, package_name):
        """Получение информации о пакете из npm реестра"""
        try:
            npm_registry_url = f"https://registry.npmjs.org/{package_name}"
            
            with urllib.request.urlopen(npm_registry_url) as response:
                data = json.loads(response.read().decode())
            
            if 'dist-tags' in data and 'latest' in data['dist-tags']:
                latest_version = data['dist-tags']['latest']
                version_data = data['versions'][latest_version]
                dependencies = version_data.get('dependencies', {})
                
                return {
                    'name': package_name,
                    'version': latest_version,
                    'dependencies': dependencies
                }
            else:
                raise Exception(f"Не удалось найти версию пакета {package_name}")
                
        except Exception as e:
            raise Exception(f"Ошибка при получении пакета {package_name}: {e}")
    
    def get_package_info_from_file(self, package_name, file_path):
        """Получение информации о пакете из тестового файла"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if package_name in data:
                package_info = data[package_name]
            else:
                # Возвращаем базовую информацию вместо ошибки
                return {
                    'name': package_name,
                    'version': 'unknown',
                    'dependencies': {}
                }
            
            return {
                'name': package_name,
                'version': package_info.get('version', '1.0.0'),
                'dependencies': package_info.get('dependencies', {})
            }
            
        except Exception as e:
            print(f"Ошибка при чтении тестового файла: {e}")
            # Возвращаем базовую информацию при ошибке
            return {
                'name': package_name,
                'version': 'unknown',
                'dependencies': {}
            }
    
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
                package_info = self.get_package_info_from_npm(current_package)
            
            dependencies = package_info.get('dependencies', {})
            
            # Сохраняем зависимости в графе
            self.dependency_graph[current_package] = {
                'version': package_info.get('version', 'unknown'),
                'dependencies': dependencies
            }
            
            # Обрабатываем зависимости через for, добавляем в очередь
            for dep_name in dependencies.keys():
                # Проверка на циклические зависимости
                if dep_name in self.dependency_graph and current_package in self.dependency_graph.get(dep_name, {}).get('dependencies', {}):
                    print(f"Обнаружена циклическая зависимость: {current_package} <-> {dep_name}")
                    continue
                
                # Добавляем в очередь только если еще не посещали
                if dep_name not in self.visited:
                    self.visited.add(dep_name)
                    queue.append((dep_name, depth + 1))
                    
        except Exception as e:
            print(f"Ошибка при обработке пакета {current_package}: {e}")
        
        # Рекурсивный вызов для обработки следующего пакета в очереди
        self.build_dependency_graph_bfs_recursive(queue, args, max_depth)
    
    def build_dependency_graph_bfs(self, start_package, args):
        """Обертка для запуска BFS с рекурсией"""
        queue = deque([(start_package, 0)])
        self.visited.add(start_package)
        self.build_dependency_graph_bfs_recursive(queue, args, args.depth)
    
    def generate_plantuml_code(self):
        """Генерация кода PlantUML для визуализации графа"""
        plantuml_code = [
            "@startuml",
            "skinparam monochrome true",
            "skinparam shadowing false",
            "skinparam defaultFontName Arial",
            "skinparam packageStyle rect",
            "left to right direction",
            ""
        ]
        
        # Добавляем узлы для всех пакетов
        for package, info in self.dependency_graph.items():
            version = info.get('version', 'unknown')
            plantuml_code.append(f'package "{package}\\n{version}" as {self._sanitize_id(package)}')
        
        plantuml_code.append("")
        
        # Добавляем связи между пакетами
        for package, info in self.dependency_graph.items():
            for dep, version in info.get('dependencies', {}).items():
                if dep in self.dependency_graph:
                    plantuml_code.append(
                        f'{self._sanitize_id(package)} --> {self._sanitize_id(dep)} : {version}'
                    )
        
        plantuml_code.append("@enduml")
        return "\n".join(plantuml_code)
    
    def _sanitize_id(self, name):
        """Создание безопасного идентификатора для PlantUML"""
        return name.replace('@', '').replace('/', '_').replace('-', '_').replace('.', '_')
    
    def generate_svg_from_plantuml(self, plantuml_code, output_file):
        """Генерация SVG из кода PlantUML"""
        try:
            # Создаем временный файл для PlantUML кода
            with tempfile.NamedTemporaryFile(mode='w', suffix='.puml', delete=False) as f:
                f.write(plantuml_code)
                temp_puml = f.name
            
            # Пробуем использовать локальный PlantUML если установлен
            try:
                cmd = ['plantuml', '-tsvg', temp_puml]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                
                # Переименовываем выходной файл
                base_name = os.path.splitext(temp_puml)[0]
                generated_svg = base_name + '.svg'
                
                if os.path.exists(generated_svg):
                    os.rename(generated_svg, output_file)
                    print(f"SVG сгенерирован локально: {output_file}")
                else:
                    raise FileNotFoundError("Локальный PlantUML не сгенерировал файл")
                    
            except (subprocess.CalledProcessError, FileNotFoundError):
                # Fallback: используем онлайн сервис PlantUML
                print("Локальный PlantUML не найден, используем онлайн сервис...")
                import urllib.parse
                
                # Кодируем PlantUML код для URL
                encoded = self._encode_plantuml(plantuml_code)
                online_url = f"http://www.plantuml.com/plantuml/svg/~1{encoded}"
                
                # Скачиваем SVG
                with urllib.request.urlopen(online_url) as response:
                    with open(output_file, 'wb') as f:
                        f.write(response.read())
                
                print(f"SVG сгенерирован онлайн: {output_file}")
            
            # Удаляем временный файл
            os.unlink(temp_puml)
            
        except Exception as e:
            print(f"Ошибка генерации SVG: {e}")
            # Сохраняем PlantUML код для ручной обработки
            puml_file = output_file + '.puml'
            with open(puml_file, 'w', encoding='utf-8') as f:
                f.write(plantuml_code)
            print(f"PlantUML код сохранен в: {puml_file}")
    
    def _encode_plantuml(self, text):
        """Кодирование текста для PlantUML онлайн"""
        import zlib
        import base64
        
        # Compress the text
        compressed = zlib.compress(text.encode('utf-8'))
        # Encode in base64
        encoded = base64.b64encode(compressed).decode('ascii')
        # Re-encode for URL
        return encoded.translate(str.maketrans(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/",
            "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"
        ))
    
    def print_ascii_tree_bfs_recursive(self, queue, prefix="", visited=None):
        """Вывод ASCII-дерева зависимостей с помощью BFS с рекурсией"""
        if not queue:
            return
            
        if visited is None:
            visited = set()
        
        current_level_size = len(queue)
        next_level_queue = deque()
        
        for i, package in enumerate(queue):
            if package in visited:
                continue
                
            visited.add(package)
            
            if package in self.dependency_graph:
                version = self.dependency_graph[package].get('version', 'unknown')
                connector = "└── " if i == current_level_size - 1 else "├── "
                print(f"{prefix}{connector}{package} ({version})")
                
                # Добавляем зависимости в очередь следующего уровня
                dependencies = list(self.dependency_graph[package].get('dependencies', {}).keys())
                for dep in dependencies:
                    if dep not in visited:
                        next_level_queue.append(dep)
            else:
                connector = "└── " if i == current_level_size - 1 else "├── "
                print(f"{prefix}{connector}{package} (не раскрыто)")
        
        # Рекурсивный вызов для следующего уровня
        if next_level_queue:
            new_prefix = prefix + "    "
            self.print_ascii_tree_bfs_recursive(next_level_queue, new_prefix, visited)
    
    def print_ascii_tree(self, package):
        """Обертка для вывода ASCII-дерева с BFS рекурсией"""
        queue = deque([package])
        self.print_ascii_tree_bfs_recursive(queue)
    
    def compare_with_npm(self, package_name):
        """Сравнение с выводом npm"""
        print(f"\nСравнение с npm для пакета {package_name}:")
        print("=" * 50)
        
        try:
            # Получаем дерево зависимостей через npm
            cmd = ['npm', 'view', package_name, 'dependencies', '--json']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout.strip():
                npm_deps = json.loads(result.stdout)
                our_deps = self.dependency_graph.get(package_name, {}).get('dependencies', {})
                
                print("Наши зависимости:")
                for dep, version in sorted(our_deps.items()):
                    print(f"  {dep}: {version}")
                
                print("\nЗависимости через npm:")
                for dep, version in sorted(npm_deps.items()):
                    print(f"  {dep}: {version}")
                
                # Анализ расхождений
                our_deps_set = set(our_deps.keys())
                npm_deps_set = set(npm_deps.keys())
                
                only_in_our = our_deps_set - npm_deps_set
                only_in_npm = npm_deps_set - our_deps_set
                common = our_deps_set & npm_deps_set
                
                print(f"\nАнализ расхождений:")
                print(f"Общие зависимости: {len(common)}")
                print(f"Только у нас: {len(only_in_our)}")
                print(f"Только в npm: {len(only_in_npm)}")
                
                if only_in_our:
                    print(f"Зависимости только в нашем анализе: {', '.join(sorted(only_in_our))}")
                if only_in_npm:
                    print(f"Зависимости только в npm: {', '.join(sorted(only_in_npm))}")
                
                # Анализ версий для общих зависимостей
                version_differences = []
                for dep in common:
                    if our_deps[dep] != npm_deps[dep]:
                        version_differences.append(f"{dep}: наша версия {our_deps[dep]} vs npm {npm_deps[dep]}")
                
                if version_differences:
                    print(f"Различия в версиях:")
                    for diff in version_differences:
                        print(f"  {diff}")
                
                # Объяснение возможных причин расхождений
                if only_in_our or only_in_npm or version_differences:
                    print(f"\nВозможные причины расхождений:")
                    print("1. Кэширование данных в npm реестре")
                    print("2. Разные версии пакетов (latest vs конкретная версия)")
                    print("3. devDependencies vs dependencies")
                    print("4. peerDependencies не учитываются в нашем анализе")
                    print("5. Временные задержки в обновлении реестра")
                    
            else:
                print("Не удалось получить данные из npm")
                
        except Exception as e:
            print(f"Ошибка при сравнении с npm: {e}")
    
    def demonstrate_visualization_cases(self):
        """Демонстрация визуализации для различных пакетов"""
        demo_packages = [
            {
                "name": "React (простая структура)",
                "package": "react",
                "file": "test_react.json"
            },
            {
                "name": "Express (средняя сложность)", 
                "package": "express",
                "file": "test_express.json"
            },
            {
                "name": "Webpack (сложная структура)",
                "package": "webpack",
                "file": "test_webpack.json"
            }
        ]
        
        print("\nДемонстрация визуализации для различных пакетов:")
        print("=" * 60)
        
        for demo in demo_packages:
            print(f"\nПакет: {demo['name']}")
            print(f"Файл: {demo['file']}")
            
            if os.path.exists(demo['file']):
                # Сбрасываем состояние
                self.dependency_graph.clear()
                self.visited.clear()
                
                try:
                    # Строим граф с BFS рекурсией
                    args = argparse.Namespace(
                        test_mode=True,
                        source=demo['file'],
                        depth=3
                    )
                    self.build_dependency_graph_bfs(demo['package'], args)
                    
                    # Генерируем визуализацию
                    output_file = f"{demo['package']}_demo.svg"
                    plantuml_code = self.generate_plantuml_code()
                    self.generate_svg_from_plantuml(plantuml_code, output_file)
                    
                    # Выводим ASCII-дерево с BFS рекурсией
                    print(f"\nASCII-дерево для {demo['package']}:")
                    print("-" * 40)
                    self.print_ascii_tree(demo['package'])
                    
                    print(f"\nSVG визуализация сохранена в: {output_file}")
                    print(f"Всего узлов в графе: {len(self.dependency_graph)}")
                    
                except Exception as e:
                    print(f"Ошибка: {e}")
            else:
                print(f"Тестовый файл {demo['file']} не найден")
    
    def run(self):
        """Основной метод запуска приложения"""
        try:
            args = self.parse_arguments()
            
            # Валидация аргументов
            errors = self.validate_arguments(args)
            if errors:
                print("Ошибки конфигурации:")
                for error in errors:
                    print(f"  - {error}")
                sys.exit(1)
            
            print("Визуализатор графа зависимостей - Этап 5 (BFS с рекурсией)")
            print("=" * 50)
            print(f"Пакет: {args.package}")
            print(f"Источник: {args.source}")
            print(f"Режим тестирования: {'Да' if args.test_mode else 'Нет'}")
            print(f"Глубина анализа: {args.depth}")
            print("=" * 50)
            
            # Построение графа зависимостей с BFS рекурсией
            print(f"\nПостроение графа зависимостей (BFS с рекурсией)...")
            self.build_dependency_graph_bfs(args.package, args)
            
            print(f"Построено узлов: {len(self.dependency_graph)}")
            
            # Вывод ASCII-дерева если запрошено
            if args.ascii_tree:
                print(f"\nASCII-дерево зависимостей для {args.package} (BFS):")
                print("=" * 50)
                self.print_ascii_tree(args.package)
            
            # Генерация PlantUML и SVG
            print(f"\nГенерация визуализации...")
            plantuml_code = self.generate_plantuml_code()
            print("Код PlantUML сгенерирован")
            
            # Сохраняем PlantUML код
            puml_file = os.path.splitext(args.output)[0] + '.puml'
            with open(puml_file, 'w', encoding='utf-8') as f:
                f.write(plantuml_code)
            print(f"PlantUML код сохранен в: {puml_file}")
            
            # Генерируем SVG
            self.generate_svg_from_plantuml(plantuml_code, args.output)
            
            # Сравнение с npm если запрошено
            if args.compare_npm and not args.test_mode:
                self.compare_with_npm(args.package)
            
            # Демонстрация различных случаев
            if args.test_mode:
                self.demonstrate_visualization_cases()
            
            print(f"\nЭтап 5 завершен успешно!")
            print(f"Результаты сохранены в:")
            print(f"  - {puml_file} (PlantUML код)")
            print(f"  - {args.output} (SVG визуализация)")
            
        except Exception as e:
            print(f"Ошибка: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == "__main__":
    visualizer = DependencyVisualizer()
    visualizer.run()