#!/usr/bin/env python3
"""
Инструмент визуализации графа зависимостей пакетов
Этап 2: Сбор данных о зависимостях (исправленная версия с GitHub)
"""

import argparse
import sys
import os
import json
import urllib.request
import urllib.error
import re
from urllib.parse import urljoin

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
    
    def get_github_repo_info(self, package_name):
        """
        Получение информации о репозитории GitHub из npm registry
        """
        npm_registry_url = "https://registry.npmjs.org/"
        package_url = urljoin(npm_registry_url, package_name)
        
        try:
            with urllib.request.urlopen(package_url) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    
                    # Получаем URL репозитория из данных пакета
                    if 'repository' in data:
                        repo_info = data['repository']
                        if isinstance(repo_info, dict) and 'url' in repo_info:
                            repo_url = repo_info['url']
                            # Очищаем URL от git+ и .git
                            repo_url = repo_url.replace('git+', '').replace('.git', '')
                            return repo_url
                    
                    # Если repository не найден, пробуем homepage
                    if 'homepage' in data and 'github.com' in data['homepage']:
                        return data['homepage']
                        
        except Exception as e:
            print(f"Ошибка при получении информации о репозитории: {e}")
            
        return None
    
    def fetch_package_json_from_github(self, repo_url):
        """
        Получение package.json из репозитория GitHub
        """
        try:
            # Преобразуем URL в raw content URL
            if 'github.com' in repo_url:
                # Преобразуем https://github.com/facebook/react в https://raw.githubusercontent.com/facebook/react/main/package.json
                repo_url = repo_url.replace('https://github.com/', 'https://raw.githubusercontent.com/')
                
                # Пробуем разные возможные ветки
                branches = ['main', 'master', 'latest']
                for branch in branches:
                    package_json_url = f"{repo_url}/{branch}/package.json"
                    print(f"Попытка получить package.json из: {package_json_url}")
                    
                    try:
                        with urllib.request.urlopen(package_json_url) as response:
                            if response.status == 200:
                                data = json.loads(response.read().decode())
                                return data
                    except urllib.error.HTTPError:
                        continue
                        
        except Exception as e:
            print(f"Ошибка при получении package.json из GitHub: {e}")
            
        return None
    
    def get_dependencies_from_package_json(self, package_json):
        """
        Извлечение зависимостей из package.json
        """
        dependencies = {}
        
        try:
            dependency_types = ['dependencies', 'devDependencies', 'peerDependencies', 'optionalDependencies']
            
            for dep_type in dependency_types:
                if dep_type in package_json and package_json[dep_type]:
                    dependencies.update(package_json[dep_type])
                    print(f"Найдено {dep_type}: {len(package_json[dep_type])}")
                    
        except Exception as e:
            print(f"Ошибка при извлечении зависимостей: {e}")
            
        return dependencies
    
    def fetch_from_npm_with_fallback(self, package_name):
        """
        Попытка получить зависимости из npm registry с fallback на GitHub
        """
        print("Попытка получить данные из npm registry...")
        npm_registry_url = "https://registry.npmjs.org/"
        package_url = urljoin(npm_registry_url, package_name)
        
        try:
            with urllib.request.urlopen(package_url) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    
                    # Пробуем получить зависимости из последней версии
                    if 'dist-tags' in data and 'latest' in data['dist-tags']:
                        latest_version = data['dist-tags']['latest']
                        if 'versions' in data and latest_version in data['versions']:
                            version_data = data['versions'][latest_version]
                            dependencies = self.get_dependencies_from_package_json(version_data)
                            
                            if dependencies:
                                return dependencies
                            
            print("Зависимости не найдены в npm registry, пробуем GitHub...")
            
            # Fallback на GitHub
            repo_url = self.get_github_repo_info(package_name)
            if repo_url:
                print(f"Найден репозиторий: {repo_url}")
                package_json = self.fetch_package_json_from_github(repo_url)
                if package_json:
                    return self.get_dependencies_from_package_json(package_json)
                    
        except Exception as e:
            print(f"Ошибка при получении данных: {e}")
            
        return {}
    
    def load_test_package_data(self, file_path):
        """
        Загрузка тестовых данных из файла
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except Exception as e:
            print(f"Ошибка при чтении тестового файла: {e}")
            return None
    
    def display_dependencies(self, package_name, dependencies):
        """
        Вывод зависимостей на экран
        """
        if not dependencies:
            print(f"Прямые зависимости не найдены")
            return
            
        print(f"\nПрямые зависимости пакета '{package_name}':")
        print("-" * 50)
        
        for dep_name, dep_version in sorted(dependencies.items()):
            print(f"  {dep_name}: {dep_version}")
        
        print(f"\nВсего зависимостей: {len(dependencies)}")
    
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
            
            # Получение данных о зависимостях
            dependencies = {}
            
            if args.test_mode:
                # Режим тестирования - загрузка из файла
                print(f"\nЗагрузка тестовых данных из файла: {args.source}")
                package_data = self.load_test_package_data(args.source)
                if package_data:
                    dependencies = self.get_dependencies_from_package_json(package_data)
            else:
                # Продакшн режим - получение данных
                print(f"\nПолучение данных для пакета {args.package}...")
                dependencies = self.fetch_from_npm_with_fallback(args.package)
            
            # Вывод зависимостей (требование этапа 2)
            self.display_dependencies(args.package, dependencies)
            
            print("\nЭтап 2 завершен успешно!")
            
        except Exception as e:
            print(f"Критическая ошибка: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == "__main__":
    visualizer = DependencyVisualizer()
    visualizer.run()