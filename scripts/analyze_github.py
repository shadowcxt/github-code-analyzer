#!/usr/bin/env python3
"""
GitHub Code Analyzer - 分析GitHub仓库并生成代码分析报告
"""

import os
import re
import sys
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse

class GitHubAnalyzer:
    def __init__(self, repo_url):
        self.repo_url = repo_url
        self.temp_dir = None
        self.repo_path = None
        self.repo_info = {}

    def parse_url(self):
        """解析GitHub URL提取owner和repo名"""
        # 处理各种GitHub URL格式
        patterns = [
            r'github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$',
            r'github\.com/([^/]+)/([^/]+?)(?:\.git)?$',
        ]

        for pattern in patterns:
            match = re.search(pattern, self.repo_url)
            if match:
                owner, repo = match.groups()
                # 去掉 .git 后缀
                repo = repo.replace('.git', '')
                return owner, repo

        raise ValueError(f"无法解析GitHub URL: {self.repo_url}")

    def clone_repo(self):
        """克隆GitHub仓库到临时目录"""
        self.temp_dir = tempfile.mkdtemp(prefix="github_analyzer_")
        print(f"克隆仓库到: {self.temp_dir}")

        cmd = ["git", "clone", "--depth", "1", self.repo_url, self.temp_dir]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"克隆失败: {result.stderr}")

        self.repo_path = Path(self.temp_dir)
        print("克隆成功")

    def detect_language(self):
        """检测项目主要编程语言"""
        # 语言统计
        language_patterns = {
            'Python': ['.py'],
            'JavaScript': ['.js', '.jsx', '.mjs'],
            'TypeScript': ['.ts', '.tsx'],
            'Java': ['.java'],
            'Go': ['.go'],
            'Rust': ['.rs'],
            'C++': ['.cpp', '.cc', '.cxx', '.hpp', '.h'],
            'C': ['.c', '.h'],
            'Ruby': ['.rb'],
            'Swift': ['.swift'],
            'Kotlin': ['.kt', '.kts'],
            'PHP': ['.php'],
            'C#': ['.cs'],
            'Scala': ['.scala'],
        }

        lang_counts = {}
        total_files = 0

        for root, dirs, files in os.walk(self.repo_path):
            # 跳过隐藏目录和常见无关目录
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', 'dist', 'build']]

            for file in files:
                total_files += 1
                ext = Path(file).suffix.lower()

                for lang, exts in language_patterns.items():
                    if ext in exts:
                        lang_counts[lang] = lang_counts.get(lang, 0) + 1
                        break

        if lang_counts:
            main_lang = max(lang_counts, key=lang_counts.get)
            self.repo_info['languages'] = lang_counts
            self.repo_info['main_language'] = main_lang
        else:
            self.repo_info['languages'] = {}
            self.repo_info['main_language'] = 'Unknown'

    def detect_tech_stack(self):
        """检测技术栈（框架、依赖）"""
        tech_stack = {
            'frameworks': [],
            'dependencies': [],
            'build_tools': []
        }

        # 检测package.json
        pkg_json = self.repo_path / 'package.json'
        if pkg_json.exists():
            try:
                with open(pkg_json) as f:
                    pkg = json.load(f)
                    deps = pkg.get('dependencies', {})
                    dev_deps = pkg.get('devDependencies', {})

                    # 常见框架识别
                    framework_keywords = {
                        'react': 'React', 'vue': 'Vue', 'angular': 'Angular',
                        'next': 'Next.js', 'nuxt': 'Nuxt.js', 'express': 'Express',
                        'fastify': 'Fastify', 'koa': 'Koa', 'django': 'Django',
                        'flask': 'Flask', 'spring': 'Spring', 'laravel': 'Laravel'
                    }

                    for dep in deps:
                        dep_lower = dep.lower()
                        for kw, name in framework_keywords.items():
                            if kw in dep_lower and name not in tech_stack['frameworks']:
                                tech_stack['frameworks'].append(name)

                    tech_stack['dependencies'] = list(deps.keys())[:20]
            except:
                pass

        # 检测requirements.txt
        req_txt = self.repo_path / 'requirements.txt'
        if req_txt.exists():
            try:
                with open(req_txt) as f:
                    deps = []
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            dep = line.split('==')[0].split('>=')[0].strip()
                            deps.append(dep)
                    tech_stack['dependencies'].extend(deps[:20])
            except:
                pass

        # 检测go.mod
        go_mod = self.repo_path / 'go.mod'
        if go_mod.exists():
            try:
                with open(go_mod) as f:
                    for line in f:
                        if line.startswith('require ('):
                            tech_stack['frameworks'].append('Go Modules')
                            break
            except:
                pass

        # 检测Cargo.toml
        cargo_toml = self.repo_path / 'Cargo.toml'
        if cargo_toml.exists():
            tech_stack['frameworks'].append('Cargo/Rust')

        # 检测pom.xml
        pom_xml = self.repo_path / 'pom.xml'
        if pom_xml.exists():
            tech_stack['frameworks'].append('Maven/Java')
            tech_stack['build_tools'].append('Maven')

        # 检测build.gradle
        build_gradle = self.repo_path / 'build.gradle'
        if build_gradle.exists():
            tech_stack['build_tools'].append('Gradle')

        self.repo_info['tech_stack'] = tech_stack

    def analyze_structure(self):
        """分析目录结构"""
        structure = {}

        def walk_dir(path, prefix=""):
            items = list(path.iterdir())
            dirs = [i for i in items if i.is_dir() and not i.name.startswith('.')]
            files = [i for i in items if i.is_file() and not i.name.startswith('.')]

            # 记录当前目录下的主要文件
            key_files = [f.name for f in files if f.suffix in ['.py', '.js', '.ts', '.go', '.rs', '.java', '.rb'] or f.name in ['README.md', 'package.json', 'requirements.txt', 'Cargo.toml', 'go.mod', 'pom.xml']]
            if key_files:
                structure[prefix or 'root'] = key_files[:10]

            # 递归子目录
            for d in dirs:
                if d.name not in ['node_modules', '__pycache__', 'venv', '.git', 'dist', 'build', 'target', 'vendor']:
                    walk_dir(d, f"{prefix}/{d.name}" if prefix else d.name)

        walk_dir(self.repo_path)
        self.repo_info['structure'] = structure

    def find_entry_points(self):
        """查找入口文件和启动配置"""
        entry_points = {
            'main_files': [],
            'config_files': [],
            'test_files': []
        }

        # 常见入口文件名
        main_patterns = ['main', 'app', 'index', 'server', 'cli', 'run']
        config_patterns = ['config', 'settings', '.env', 'setup']
        test_patterns = ['test', 'spec', '__tests__']

        for root, dirs, files in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', 'dist', 'build', '.git']]

            for f in files:
                if f.startswith('.'):
                    continue

                f_lower = f.lower()
                rel_path = os.path.relpath(os.path.join(root, f), self.repo_path)

                # 入口文件
                for pattern in main_patterns:
                    if pattern in f_lower and f.endswith(('.py', '.js', '.ts', '.go', '.rs', '.java', '.rb', '.sh')):
                        entry_points['main_files'].append(rel_path)
                        break

                # 配置文件
                for pattern in config_patterns:
                    if pattern in f_lower or f in ['package.json', 'requirements.txt', 'Cargo.toml', 'go.mod', 'pom.xml', 'build.gradle', 'Makefile', 'Dockerfile']:
                        entry_points['config_files'].append(rel_path)
                        break

                # 测试文件
                for pattern in test_patterns:
                    if pattern in f_lower or f.endswith(('.test.js', '.test.ts', '.spec.js', '.spec.ts', '_test.py', '_test.go')):
                        entry_points['test_files'].append(rel_path)
                        break

        # 去重并限制数量
        entry_points['main_files'] = list(set(entry_points['main_files']))[:10]
        entry_points['config_files'] = list(set(entry_points['config_files']))[:15]
        entry_points['test_files'] = list(set(entry_points['test_files']))[:10]

        self.repo_info['entry_points'] = entry_points

    def analyze_apis(self):
        """分析API接口定义"""
        api_endpoints = []

        # 查找常见API定义
        api_patterns = ['api', 'route', 'endpoint', 'controller']

        for root, dirs, files in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if not d.startswith('.')]

            for f in files:
                if f.startswith('.'):
                    continue

                rel_path = os.path.relpath(os.path.join(root, f), self.repo_path)
                f_lower = f.lower()

                for pattern in api_patterns:
                    if pattern in f_lower:
                        api_endpoints.append(rel_path)
                        break

        self.repo_info['api_files'] = api_endpoints[:15]

    def read_readme(self):
        """读取README获取项目描述"""
        readme_files = ['README.md', 'README.txt', 'README', 'readme.md']

        for rf in readme_files:
            readme_path = self.repo_path / rf
            if readme_path.exists():
                try:
                    with open(readme_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # 取前2000字符
                        self.repo_info['readme'] = content[:2000]
                        return
                except:
                    pass

        self.repo_info['readme'] = ""

    def analyze(self):
        """执行完整分析"""
        try:
            print("开始分析...")

            # 1. 克隆仓库
            self.clone_repo()

            # 2. 读取README
            self.read_readme()

            # 3. 检测语言
            self.detect_language()

            # 4. 检测技术栈
            self.detect_tech_stack()

            # 5. 分析结构
            self.analyze_structure()

            # 6. 查找入口点
            self.find_entry_points()

            # 7. 分析API
            self.analyze_apis()

            print("分析完成!")
            return self.repo_info

        finally:
            # 清理临时目录
            if self.temp_dir and os.path.exists(self.temp_dir):
                try:
                    shutil.rmtree(self.temp_dir)
                    print(f"已清理临时目录: {self.temp_dir}")
                except:
                    pass

def main():
    if len(sys.argv) < 2:
        print("用法: python analyze_github.py <github_url>")
        sys.exit(1)

    repo_url = sys.argv[1]
    analyzer = GitHubAnalyzer(repo_url)

    try:
        result = analyzer.analyze()
        print("\n=== 分析结果 ===")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
