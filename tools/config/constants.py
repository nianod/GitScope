"""Shared runtime flags and analysis configuration."""

import os
import sys
import json
import csv
import argparse
import hashlib
import re
import subprocess
import time
import logging
import multiprocessing
import threading
import datetime
import random
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple, Optional, Any

try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    from github import Github, RateLimitExceededException, GithubException

    HAS_PYGITHUB = True
except ImportError:
    HAS_PYGITHUB = False

    class GithubException(Exception):
        pass

    class RateLimitExceededException(GithubException):
        pass

    class Github:
        pass


CSV_LOCK = threading.Lock()

try:
    import tiktoken

    HAS_TIKTOKEN = True
    ENCODING = tiktoken.get_encoding("cl100k_base")
except ImportError:
    HAS_TIKTOKEN = False
    ENCODING = None

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

MAX_FILE_BYTES = 5 * 1024 * 1024
SIMILARITY_THRESHOLD = 0.85
MIN_LOC = 3
MIN_TOKENS = 20
MAX_SIMILARITY_PAIRS = 50_000
MAX_BUCKET_COMPARE = 300

GIT_LOG_TIMEOUT = 120
CODE_AGE_THRESHOLDS_YEARS = [1, 2]
REQUIRED_SCC_VERSION = "3.7.0"


RATING_CRITERIA = {
    "commits": {"min": 75, "preferred": 200, "weight": 0.20},
    "dev_span_months": {"min": 6, "preferred": 24, "weight": 0.15},
    "contributors": {"min": 2, "preferred": 5, "weight": 0.15},
    "loc": {"min": 5_000, "preferred": 50_000, "weight": 0.20},
    "has_tests": {"weight": 0.10},
    "has_ci": {"weight": 0.10},
    "test_file_count": {"min": 20, "preferred": 200, "weight": 0.05},
    "source_file_ratio": {"min": 0.40, "preferred": 0.60, "weight": 0.05},
}

FRAMEWORK_MANIFEST_PARSERS = {
    "package.json": [
        "react",
        "vue",
        "angular",
        "svelte",
        "next",
        "nuxt",
        "gatsby",
        "remix",
        "astro",
        "express",
        "fastify",
        "nestjs",
        "koa",
        "hapi",
    ],
    "requirements.txt": [
        "django",
        "flask",
        "fastapi",
        "tornado",
        "starlette",
        "aiohttp",
        "pyramid",
        "falcon",
        "bottle",
    ],
    "Pipfile": ["django", "flask", "fastapi"],
    "pom.xml": ["spring", "springboot", "quarkus", "micronaut"],
    "build.gradle": ["spring", "springboot", "quarkus", "micronaut"],
    "Cargo.toml": ["actix", "axum", "warp", "rocket"],
    "go.mod": ["gin", "echo", "fiber", "chi", "beego"],
    "Gemfile": ["rails", "sinatra", "hanami"],
    "composer.json": ["laravel", "symfony", "codeigniter", "yii"],
    "mix.exs": ["phoenix"],
    "stack.yaml": ["yesod", "scotty"],
}

IMPORT_FRAMEWORK_MAP = {
    "py": {
        "django": "Django",
        "flask": "Flask",
        "fastapi": "FastAPI",
        "tornado": "Tornado",
        "starlette": "Starlette",
        "aiohttp": "aiohttp",
        "pyramid": "Pyramid",
        "falcon": "Falcon",
        "bottle": "Bottle",
    },
    "js": {
        "express": "Express",
        "next": "Next.js",
        "react": "React",
        "vue": "Vue",
        "angular": "Angular",
        "fastify": "Fastify",
        "nestjs": "NestJS",
        "koa": "Koa",
        "hapi": "Hapi",
    },
    "jsx": {"react": "React"},
    "tsx": {"react": "React", "next": "Next.js"},
}

FRONTEND_FRAMEWORKS = {
    "react",
    "vue",
    "angular",
    "svelte",
    "next",
    "nuxt",
    "gatsby",
    "remix",
    "astro",
}

BACKEND_FRAMEWORKS = {
    "express",
    "fastify",
    "nestjs",
    "koa",
    "hapi",
    "django",
    "flask",
    "fastapi",
    "tornado",
    "starlette",
    "aiohttp",
    "pyramid",
    "falcon",
    "bottle",
    "spring",
    "springboot",
    "quarkus",
    "micronaut",
    "actix",
    "axum",
    "warp",
    "rocket",
    "gin",
    "echo",
    "fiber",
    "chi",
    "beego",
    "rails",
    "sinatra",
    "hanami",
    "laravel",
    "symfony",
    "codeigniter",
    "yii",
    "phoenix",
    "yesod",
    "scotty",
}

EXT_TO_LANG_MAP = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JSX",
    ".ts": "TypeScript",
    ".tsx": "TSX",
    ".go": "Go",
    ".java": "Java",
    ".c": "C",
    ".cpp": "C++",
    ".cc": "C++",
    ".h": "C/C++ Header",
    ".hpp": "C/C++ Header",
    ".cs": "C#",
    ".rb": "Ruby",
    ".php": "PHP",
    ".rs": "Rust",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sass": "Sass",
    ".less": "LESS",
    ".sql": "SQL",
    ".sh": "Bourne Shell",
    ".ps1": "PowerShell",
    ".bat": "DOS Batch",
    ".json": "JSON",
    ".xml": "XML",
    ".md": "Markdown",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".scala": "Scala",
    ".lua": "Lua",
}

FORMAL_FRAMEWORK_NAMES = {
    "react": "React",
    "next": "Next.js",
    "vue": "Vue",
    "angular": "Angular",
    "svelte": "Svelte",
    "express": "Express",
    "fastapi": "FastAPI",
    "django": "Django",
    "flask": "Flask",
    "spring": "Spring Boot",
    "springboot": "Spring Boot",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "mongodb": "MongoDB",
    "redis": "Redis",
    "mysql": "MySQL",
    "sqlite": "SQLite",
    "firebase": "Firebase",
    "jest": "Jest",
    "vitest": "Vitest",
    "cypress": "Cypress",
    "playwright": "Playwright",
}

LANG_MERGE_MAP = {
    "C/C++ Header": "C++",
    "Jupyter Notebook": "Python",
    "JSX": "JavaScript",
    "TSX": "TypeScript",
}

FRONTEND_LANGUAGES = {
    "HTML",
    "CSS",
    "SCSS",
    "Sass",
    "Less",
    "JavaScript",
    "TypeScript",
    "JSX",
    "TSX",
    "Vue",
    "Svelte",
}

BACKEND_LANGUAGES = {
    "Python",
    "Java",
    "Go",
    "Rust",
    "Ruby",
    "PHP",
    "C++",
    "C",
    "C#",
    "Scala",
    "Kotlin",
    "Elixir",
    "Haskell",
    "Perl",
    "Clojure",
    "SQL",
    "Swift",
    "Dart",
}

NON_CORE_FORMATS = {
    "JSON",
    "XML",
    "YAML",
    "CSV",
    "TOML",
    "INI",
    "Protocol Buffers",
    "Graphviz (DOT)",
    "SVG",
    "SQL",
    "Properties",
    "Excel",
    "Parquet",
    "HCL",
    "Starlark",
    "Markdown",
    "Text",
    "Plain Text",
    "reStructuredText",
    "AsciiDoc",
    "Doxygen",
    "Org",
    "TeX",
    "Org Mode",
    "Gradle",
    "ProGuard",
    "Windows Resource File",
    "Maven POM",
    "Protocol Buffers",
    "PowerShell",
    "Bourne Shell",
    "Bourne Again Shell",
    "Fish Shell",
    "DOS Batch",
    "make",
    "CMake",
    "Dockerfile",
    "Vagrantfile",
    "Procfile",
    "Rakefile",
    "Gemfile",
    "Pipfile",
    "BitBake",
    "Meson",
    "Kconfig",
    "QMake",
    "Bazel",
    "LESS",
    "SCSS",
    "Sass",
    "Stylus",
    "PostCSS",
}

BOILERPLATE_FILES = {
    "reportwebvitals.js",
    "setuptests.js",
    "app.test.js",
    "logo.svg",
    "favicon.ico",
    "service-worker.js",
    "manifest.json",
    "robots.txt",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "manage.py",
    "asgi.py",
    "wsgi.py",
    "__init__.py",
    "mvnw",
    "mvnw.cmd",
    "gradlew",
    "gradlew.bat",
    "settings.gradle",
    "gradle-wrapper.properties",
    "artisan",
    "server.php",
    "bundle",
    "rails",
    "rake",
    "setup",
}

VENDORED_NAMES = {
    "jquery",
    "bootstrap",
    "angular",
    "react.production",
    "react-dom.production",
    "vue.global",
    "vue.runtime",
    "lodash",
    "underscore",
    "backbone",
    "d3",
    "three",
    "moment",
    "chart",
    "highcharts",
    "leaflet",
    "popper",
    "tether",
    "select2",
    "datatables",
    "tinymce",
    "ckeditor",
    "ace-editor",
    "codemirror",
    "quill",
    "summernote",
    "sweetalert",
    "toastr",
    "animate",
    "font-awesome",
    "normalize",
    "reset",
    "polyfill",
    "modernizr",
    "respond",
    "html5shiv",
    "pace",
    "hammer",
    "howler",
    "socket.io",
    "fabric",
    "konva",
    "excalidraw",
    "wiris",
    "mathjax",
    "katex",
    "zoom-meeting",
    "dropbox-sdk",
    "aws-sdk",
    "firebase-app",
    "firebase-auth",
    "multislider",
}

VENDORED_DIRS = {
    "/vendor/",
    "/vendors/",
    "/third_party/",
    "/third-party/",
    "/bower_components/",
    "/jspm_packages/",
    "/web_modules/",
    "/custom_node_modules/",
    "/extern/",
    "/external/",
    "/lib/vendor/",
    "/.bundle/",
    "/cache/",
    "/deps/",
    "/site-packages/",
    "/dist-packages/",
    "/_vendor/",
}

BUNDLE_PATTERNS = {
    "bundle.js",
    "chunk.js",
    "vendor.js",
    "vendors.js",
    "runtime.js",
    "main.chunk.js",
    "vendors~main",
}

# Stage 4: Infrastructure & Service Detection
INFRASTRUCTURE_INDICATORS = {
    "databases": [
        "postgres",
        "postgresql",
        "mysql",
        "mongodb",
        "redis",
        "sqlite",
        "elasticsearch",
        "dynamodb",
        "mariadb",
        "oracle",
        "mssql",
        "cassandra",
        "neo4j",
        "couchdb",
        "prisma",
        "sequelize",
        "mongoose",
        "psycopg2",
        "psycopg",
        "sqlalchemy",
        "typeorm",
        "knex",
        "tortoise-orm",
        "dj-database-url",
        "supabase",
        "pocketbase",
        "surrealdb",
        "cockroachdb",
        "fauna",
        "influxdb",
        "snowflake",
        "clickhouse",
        "databricks",
        "firebird",
        "trino",
        "presto",
    ],
    "deployment": [
        "docker",
        "kubernetes",
        "aws",
        "azure",
        "gcp",
        "heroku",
        "vercel",
        "netlify",
        "terraform",
        "ansible",
        "jenkins",
        "travis",
        "circleci",
        "github actions",
        "dockerfile",
        "docker-compose",
    ],
    "apis": [
        "stripe",
        "twilio",
        "sendgrid",
        "openai",
        "firebase",
        "auth0",
        "slack",
        "aws-sdk",
        "google-cloud",
        "mailgun",
        "algolia",
        "pusher",
    ],
}

INFRA_MANIFESTS_TO_CHECK = [
    "package.json",
    "requirements.txt",
    "Pipfile",
    "pom.xml",
    "build.gradle",
    "Cargo.toml",
    "go.mod",
    "Gemfile",
    "composer.json",
    "docker-compose.yml",
]
INFRA_CONFIG_FILES_TO_CHECK = [
    ".env",
    "settings.py",
    "config.js",
    "web.config",
    "appsettings.json",
    "config.php",
    "configuration.yaml",
]

INFRA_DB_EXTENSIONS = {".db", ".sqlite", ".sqlite3", ".mdb", ".accdb", ".rdb"}

INFRA_CODE_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".php",
    ".go",
    ".java",
    ".rb",
    ".cs",
    ".sql",
}

INFRA_CONN_MAP = {
    "postgres://": "postgres",
    "postgresql://": "postgres",
    "mysql://": "mysql",
    "mongodb://": "mongodb",
    "redis://": "redis",
}

INFRA_FILE_MAP = {
    "dockerfile": ("deployment", "docker"),
    "docker-compose": ("deployment", "docker-compose"),
    "jenkinsfile": ("deployment", "jenkins"),
    ".travis.yml": ("deployment", "travis"),
    "circle.yml": ("deployment", "circleci"),
    "terraform": ("deployment", "terraform"),
    ".github/workflows": ("deployment", "github actions"),
}

INFRA_CANONICAL_MAP = {
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "psycopg2": "PostgreSQL",
    "psycopg": "PostgreSQL",
    "mongodb": "MongoDB",
    "mongoose": "MongoDB",
    "mysql": "MySQL",
    "mariadb": "MariaDB",
    "sqlite": "SQLite",
    "redis": "Redis",
    "elasticsearch": "Elasticsearch",
    "dynamodb": "DynamoDB",
    "cassandra": "Cassandra",
    "oracle": "Oracle",
    "mssql": "SQL Server",
    "neo4j": "Neo4j",
    "couchdb": "CouchDB",
    "firebase": "Firebase",
    "firestore": "Firebase",
    "prisma": "Prisma (ORM)",
    "sequelize": "Sequelize (ORM)",
    "sqlalchemy": "SQLAlchemy (ORM)",
    "typeorm": "TypeORM",
    "knex": "Knex.js",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "github actions": "GitHub Actions",
    "docker-compose": "Docker Compose",
}

DOC_SETUP_KEYWORDS = ["setup", "install", "getting started", "running", "requirements"]

COVERAGE_FILES = [
    "lcov.info",
    "coverage.xml",
    "cobertura.xml",
    ".coverage",
    "coverage/index.html",
]

# Stage 4: Testing & Quality Patterns
TEST_CASE_PATTERNS = {
    "python": re.compile(r"def\s+test_"),
    "javascript": re.compile(r"(it|test)\s*\("),
    "typescript": re.compile(r"(it|test)\s*\("),
    "java": re.compile(r"@Test"),
    "go": re.compile(r"func\s+Test"),
    "php": re.compile(r"public\s+function\s+test"),
    "ruby": re.compile(r"test\s+['\"]"),
}

# Stage 5: Secret / credential scanning patterns
SECRET_PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("AWS Access Key", re.compile(r"AKIA[0-9A-Z]{16}")),
    (
        "AWS Secret Key",
        re.compile(r"(?i)aws.{0,20}secret.{0,20}['\"][0-9a-zA-Z/+]{40}['\"]"),
    ),
    ("GitHub Token", re.compile(r"ghp_[0-9a-zA-Z]{36}")),
    ("GitHub OAuth", re.compile(r"gho_[0-9a-zA-Z]{36}")),
    ("GitHub App Token", re.compile(r"ghu_[0-9a-zA-Z]{36}")),
    ("Slack Token", re.compile(r"xox[baprs]-[0-9a-zA-Z\-]{10,48}")),
    ("Google API Key", re.compile(r"AIza[0-9A-Za-z\-_]{35}")),
    ("Stripe Secret Key", re.compile(r"sk_live_[0-9a-zA-Z]{24,}")),
    ("Stripe Public Key", re.compile(r"pk_live_[0-9a-zA-Z]{24,}")),
    (
        "Private Key Block",
        re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    ),
    (
        "Generic Password",
        re.compile(r"(?i)(password|passwd|pwd)\s*[=:]\s*['\"][^'\"]{6,}['\"]"),
    ),
    (
        "Generic API Key",
        re.compile(r"(?i)(api_key|apikey|api-key)\s*[=:]\s*['\"][^'\"]{8,}['\"]"),
    ),
    ("Generic Secret", re.compile(r"(?i)(secret|token)\s*[=:]\s*['\"][^'\"]{8,}['\"]")),
    (
        "DB Connection String",
        re.compile(r"(?i)(mongodb|postgres|mysql|redis)://[^\s'\"]{10,}"),
    ),
    ("Bearer Token", re.compile(r"(?i)bearer\s+[0-9a-zA-Z\-._~+/]{20,}")),
]

SECRET_SCAN_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".go",
    ".rb",
    ".php",
    ".java",
    ".kt",
    ".cs",
    ".env",
    ".sh",
    ".bash",
    ".yml",
    ".yaml",
    ".toml",
    ".ini",
    ".cfg",
    ".conf",
    ".json",
}

SECRET_SCAN_SKIP = {".lock", ".sum", ".mod"}

# Language name mapping (extension → display name)
EXT_TO_LANGUAGE: Dict[str, str] = {
    ".c": "C",
    ".h": "C",
    ".cpp": "C++",
    ".hpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".c++": "C++",
    ".hxx": "C++",
    ".h++": "C++",
    ".C": "C++",
    ".H": "C++",
    ".py": "Python",
    ".pyw": "Python",
    ".pyx": "Python",
    ".pxd": "Python",
    ".pyi": "Python",
    ".js": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".java": "Java",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".scala": "Scala",
    ".groovy": "Groovy",
    ".gradle": "Groovy",
    ".clj": "Clojure",
    ".cljs": "Clojure",
    ".cljc": "Clojure",
    ".edn": "Clojure",
    ".cs": "C#",
    ".fs": "F#",
    ".fsx": "F#",
    ".fsi": "F#",
    ".go": "Go",
    ".rs": "Rust",
    ".swift": "Swift",
    ".m": "Objective-C",
    ".mm": "Objective-C",
    ".zig": "Zig",
    ".nim": "Nim",
    ".v": "V",
    ".d": "D",
    ".ada": "Ada",
    ".adb": "Ada",
    ".ads": "Ada",
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
    ".fish": "Shell",
    ".ksh": "Shell",
    ".csh": "Shell",
    ".tcsh": "Shell",
    ".bat": "Batch",
    ".cmd": "Batch",
    ".ps1": "PowerShell",
    ".rb": "Ruby",
    ".erb": "Ruby",
    ".rake": "Ruby",
    ".php": "PHP",
    ".php3": "PHP",
    ".php4": "PHP",
    ".php5": "PHP",
    ".phtml": "PHP",
    ".pl": "Perl",
    ".pm": "Perl",
    ".t": "Perl",
    ".pod": "Perl",
    ".lua": "Lua",
    ".r": "R",
    ".R": "R",
    ".hs": "Haskell",
    ".lhs": "Haskell",
    ".ml": "OCaml",
    ".mli": "OCaml",
    ".erl": "Erlang",
    ".hrl": "Erlang",
    ".ex": "Elixir",
    ".exs": "Elixir",
    ".elm": "Elm",
    ".lisp": "Lisp",
    ".lsp": "Lisp",
    ".cl": "Lisp",
    ".el": "Lisp",
    ".scm": "Scheme",
    ".ss": "Scheme",
    ".rkt": "Scheme",
    ".re": "ReasonML",
    ".rei": "ReasonML",
    ".purs": "PureScript",
    ".dart": "Dart",
    ".jl": "Julia",
    ".f": "Fortran",
    ".for": "Fortran",
    ".f90": "Fortran",
    ".f95": "Fortran",
    ".f03": "Fortran",
    ".f08": "Fortran",
    ".sol": "Solidity",
    ".move": "Move",
    ".vh": "Verilog",
    ".sv": "Verilog",
    ".vhd": "VHDL",
    ".vhdl": "VHDL",
    ".asm": "Assembly",
    ".s": "Assembly",
    ".S": "Assembly",
    ".vue": "Vue",
    ".svelte": "Svelte",
    ".jsp": "JSP",
    ".asp": "ASP",
    ".aspx": "ASP.NET",
    ".sql": "SQL",
    ".psql": "SQL",
    ".mysql": "SQL",
    ".pgsql": "SQL",
    ".graphql": "GraphQL",
    ".gql": "GraphQL",
    ".proto": "Protobuf",
    ".tf": "Terraform",
    ".tfvars": "Terraform",
    ".hcl": "HCL",
    ".sls": "SaltStack",
    ".ipynb": "Jupyter",
    ".pas": "Pascal",
    ".pp": "Pascal",
    ".inc": "Pascal",
    ".cob": "COBOL",
    ".cbl": "COBOL",
    ".cpy": "COBOL",
    ".cr": "Crystal",
    ".vim": "Vimscript",
    ".tcl": "Tcl",
    ".awk": "AWK",
    ".sed": "Sed",
    ".mk": "Makefile",
    ".cmake": "CMake",
    ".hack": "Hack",
    ".hh": "Hack",
    ".groovy": "Groovy",
}

OPENSOURCE_LICENSE_FILES = {
    "license",
    "license.txt",
    "license.md",
    "license.rst",
    "licence",
    "licence.txt",
    "licence.md",
    "copying",
    "copying.txt",
    "copying.md",
}

OPENSOURCE_SPDX_INDICATORS = [
    "mit license",
    "apache license",
    "gnu general public",
    "bsd license",
    "bsd 3-clause",
    "bsd 2-clause",
    "mozilla public",
    "isc license",
    "creative commons",
    "the unlicense",
    "eclipse public",
    "european union public",
    "common development",
]

SKIP_DIRS = {
    ".git",
    "node_modules",
    "vendor",
    "vendors",
    "__pycache__",
    "env",
    "venv",
    ".venv",
    ".tox",
    "build",
    "dist",
    ".idea",
    ".vscode",
    ".next",
    ".nuxt",
    ".svelte-kit",
    ".output",
    ".cache",
    ".parcel-cache",
    "out",
    "coverage",
    ".pytest_cache",
    ".mypy_cache",
    ".env",
    "virtualenv",
    "conda-env",
    "site-packages",
    "dist-packages",
    ".yarn",
    ".pnp",
    "bower_components",
    "jspm_packages",
    "web_modules",
    "migrations",
    "alembic",
    "test",
    "tests",
    "spec",
    "specs",
    "examples",
    "samples",
    "demo",
    "benchmarks",
    "screenshots",
    "Lib",
    "lib64",
    "Scripts",
    "bin",
    "Include",
    "obj",
    "third_party",
    "third-party",
    "extern",
    "external",
    "custom_node_modules",
}

SKIP_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".gitignore",
    ".gitmodules",
    ".zip",
    ".tar",
    ".gz",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".pdf",
    ".mp4",
    ".mp3",
    ".ttf",
    ".woff",
    ".woff2",
    ".eot",
    ".otf",
    ".ico",
    ".svg",
    ".webp",
    ".bmp",
    ".json",
    ".md",
    ".markdown",
    ".txt",
    ".yaml",
    ".yml",
    ".toml",
    ".xml",
    ".csv",
    ".tsv",
    ".diff",
    ".patch",
    ".org",
    ".rc",
    ".pro",
    ".properties",
    ".gradle",
    ".pom",
}

C_EXTENSIONS = {".c", ".h"}
CPP_EXTENSIONS = {".cpp", ".hpp", ".cc", ".cxx", ".c++", ".hxx", ".h++", ".C", ".H"}
PYTHON_EXTENSIONS = {".py", ".pyw", ".pyx", ".pxd", ".pyi"}
JAVASCRIPT_EXTENSIONS = {".js", ".mjs", ".cjs"}
TYPESCRIPT_EXTENSIONS = {".ts", ".tsx"}
JSX_EXTENSIONS = {".jsx"}
FRONTEND_FRAMEWORK_EXTENSIONS = {".vue", ".svelte"}
JAVA_EXTENSIONS = {".java"}
KOTLIN_EXTENSIONS = {".kt", ".kts"}
SCALA_EXTENSIONS = {".scala"}
GROOVY_EXTENSIONS = {".groovy", ".gradle"}
CLOJURE_EXTENSIONS = {".clj", ".cljs", ".cljc", ".edn"}
CSHARP_EXTENSIONS = {".cs"}
FSHARP_EXTENSIONS = {".fs", ".fsx", ".fsi"}
GO_EXTENSIONS = {".go"}
RUST_EXTENSIONS = {".rs"}
SWIFT_EXTENSIONS = {".swift"}
OBJC_EXTENSIONS = {".m", ".mm"}
UNIX_SHELL_EXTENSIONS = {".sh", ".bash", ".zsh", ".fish", ".ksh", ".csh", ".tcsh"}
WINDOWS_SHELL_EXTENSIONS = {".bat", ".cmd", ".ps1"}
RUBY_EXTENSIONS = {".rb", ".erb", ".rake"}
PHP_EXTENSIONS = {".php", ".php3", ".php4", ".php5", ".phtml"}
PERL_EXTENSIONS = {".pl", ".pm", ".t", ".pod"}
LUA_EXTENSIONS = {".lua"}
R_EXTENSIONS = {".r", ".R"}
HASKELL_EXTENSIONS = {".hs", ".lhs"}
OCAML_EXTENSIONS = {".ml", ".mli"}
ERLANG_EXTENSIONS = {".erl", ".hrl"}
ELIXIR_EXTENSIONS = {".ex", ".exs"}
ELM_EXTENSIONS = {".elm"}
DART_EXTENSIONS = {".dart"}
JULIA_EXTENSIONS = {".jl"}
NIM_EXTENSIONS = {".nim"}
CRYSTAL_EXTENSIONS = {".cr"}
ZIG_EXTENSIONS = {".zig"}
V_EXTENSIONS = {".v"}
VERILOG_EXTENSIONS = {".vh", ".sv"}
VHDL_EXTENSIONS = {".vhd", ".vhdl"}
ASSEMBLY_EXTENSIONS = {".asm", ".s", ".S"}
SOLIDITY_EXTENSIONS = {".sol"}
MOVE_EXTENSIONS = {".move"}
WEB_TEMPLATE_EXTENSIONS = {".jsp", ".asp", ".aspx"}
SQL_EXTENSIONS = {".sql", ".psql", ".mysql", ".pgsql"}
GRAPHQL_EXTENSIONS = {".graphql", ".gql"}
PROTOBUF_EXTENSIONS = {".proto"}
TERRAFORM_EXTENSIONS = {".tf", ".tfvars", ".hcl"}
SALT_EXTENSIONS = {".sls"}
JUPYTER_EXTENSIONS = {".ipynb"}
PASCAL_EXTENSIONS = {".pas", ".pp", ".inc"}
FORTRAN_EXTENSIONS = {".f", ".for", ".f90", ".f95", ".f03", ".f08"}
COBOL_EXTENSIONS = {".cob", ".cbl", ".cpy"}
ADA_EXTENSIONS = {".ada", ".adb", ".ads"}
D_EXTENSIONS = {".d"}
LISP_EXTENSIONS = {".lisp", ".lsp", ".cl", ".el"}
SCHEME_EXTENSIONS = {".scm", ".ss", ".rkt"}
VIM_EXTENSIONS = {".vim"}
TCL_EXTENSIONS = {".tcl"}
AWK_EXTENSIONS = {".awk"}
SED_EXTENSIONS = {".sed"}
MAKEFILE_EXTENSIONS = {".mk"}
CMAKE_EXTENSIONS = {".cmake"}
HACK_EXTENSIONS = {".hack", ".hh"}
REASON_EXTENSIONS = {".re", ".rei"}
PURESCRIPT_EXTENSIONS = {".purs"}

CODE_EXTENSIONS = (
    C_EXTENSIONS
    | CPP_EXTENSIONS
    | PYTHON_EXTENSIONS
    | JAVASCRIPT_EXTENSIONS
    | TYPESCRIPT_EXTENSIONS
    | JSX_EXTENSIONS
    | FRONTEND_FRAMEWORK_EXTENSIONS
    | JAVA_EXTENSIONS
    | KOTLIN_EXTENSIONS
    | SCALA_EXTENSIONS
    | GROOVY_EXTENSIONS
    | CLOJURE_EXTENSIONS
    | CSHARP_EXTENSIONS
    | FSHARP_EXTENSIONS
    | GO_EXTENSIONS
    | RUST_EXTENSIONS
    | SWIFT_EXTENSIONS
    | OBJC_EXTENSIONS
    | UNIX_SHELL_EXTENSIONS
    | WINDOWS_SHELL_EXTENSIONS
    | RUBY_EXTENSIONS
    | PHP_EXTENSIONS
    | PERL_EXTENSIONS
    | LUA_EXTENSIONS
    | R_EXTENSIONS
    | HASKELL_EXTENSIONS
    | OCAML_EXTENSIONS
    | ERLANG_EXTENSIONS
    | ELIXIR_EXTENSIONS
    | ELM_EXTENSIONS
    | DART_EXTENSIONS
    | JULIA_EXTENSIONS
    | NIM_EXTENSIONS
    | CRYSTAL_EXTENSIONS
    | ZIG_EXTENSIONS
    | V_EXTENSIONS
    | VERILOG_EXTENSIONS
    | VHDL_EXTENSIONS
    | ASSEMBLY_EXTENSIONS
    | SOLIDITY_EXTENSIONS
    | MOVE_EXTENSIONS
    | WEB_TEMPLATE_EXTENSIONS
    | SQL_EXTENSIONS
    | GRAPHQL_EXTENSIONS
    | PROTOBUF_EXTENSIONS
    | TERRAFORM_EXTENSIONS
    | SALT_EXTENSIONS
    | JUPYTER_EXTENSIONS
    | PASCAL_EXTENSIONS
    | FORTRAN_EXTENSIONS
    | COBOL_EXTENSIONS
    | ADA_EXTENSIONS
    | D_EXTENSIONS
    | LISP_EXTENSIONS
    | SCHEME_EXTENSIONS
    | VIM_EXTENSIONS
    | TCL_EXTENSIONS
    | AWK_EXTENSIONS
    | SED_EXTENSIONS
    | MAKEFILE_EXTENSIONS
    | CMAKE_EXTENSIONS
    | HACK_EXTENSIONS
    | REASON_EXTENSIONS
    | PURESCRIPT_EXTENSIONS
)

NON_CODE_EXTENSIONS = {
    ".md",
    ".markdown",
    ".rst",
    ".txt",
    ".adoc",
    ".tex",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".conf",
    ".xml",
    ".csv",
    ".tsv",
    ".dat",
    ".log",
    ".tmp",
    ".temp",
    ".bak",
    ".swp",
    ".swo",
    ".lock",
    ".pem",
    ".crt",
    ".key",
    ".cer",
    ".tar",
    ".gz",
    ".bz2",
    ".xz",
    ".7z",
    ".rar",
}

DOC_TEXT_EXTENSIONS = {".md", ".markdown", ".rst", ".txt", ".adoc", ".tex"}
CONFIG_TEXT_EXTENSIONS = {
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".conf",
    ".xml",
}
LLM_TEXT_EXTENSIONS = DOC_TEXT_EXTENSIONS | CONFIG_TEXT_EXTENSIONS

SCC_NON_AUTHORED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "vendor",
    "node_modules",
    "dist",
    "build",
    "generated",
    "migrations",
    "autogen",
    "auto-generated",
    "generated-src",
    "generated-code",
    "__pycache__",
    ".pytest_cache",
    "obj",
    "coverage",
    ".nyc_output",
    ".next",
    ".nuxt",
    ".gradle",
    ".cxx",
    "Pods",
    "DerivedData",
    "vendor_prefixed",
    "vendor8",
    "bower_components",
    "generated-sources",
    "intermediates",
    ".idea",
    ".kotlin",
    ".vite",
    ".cache",
}


SCC_NON_SOURCE_LANGUAGES = {
    "JSON",
    "XML",
    "YAML",
    "CSV",
    "TOML",
    "INI",
    "Plain Text",
    "Text",
    "Markdown",
    "reStructuredText",
    "AsciiDoc",
    "Doxygen",
    "Org",
    "Org Mode",
    "TeX",
    "SVG",
    "Properties",
    "Excel",
    "Parquet",
    "License",
}

SPECIAL_CODE_FILES = {
    "dockerfile": "code",
    "makefile": "code",
    "gnumakefile": "code",
    "rakefile": "code",
    "gemfile": "code",
    "vagrantfile": "code",
    "jenkinsfile": "code",
    "podfile": "code",
    "brewfile": "code",
    "cakefile": "code",
    "guardfile": "code",
    "fastfile": "code",
    "dangerfile": "code",
}

EXCLUDED_SPECIAL_FILES = {
    "readme",
    "license",
    "licence",
    "changelog",
    "changes",
    "authors",
    "contributors",
    "notice",
    "patents",
    "copying",
    "todo",
    "history",
    "news",
    "thanks",
    "credits",
    "citation",
}

CONFIG_FILENAMES = {
    "requirements.txt",
    "package.json",
    "pom.xml",
    "build.gradle",
    "cargo.toml",
    "dockerfile",
    "makefile",
    "setup.py",
    "gemfile",
    "rakefile",
    "podfile",
}

CI_FILENAMES = {
    ".gitlab-ci.yml",
    ".gitlab-ci.yaml",
    "circle.yml",
    ".circleci",
    "azure-pipelines.yml",
    "azure-pipelines.yaml",
    ".travis.yml",
    "appveyor.yml",
    "jenkinsfile",
}

CI_DIRECTORIES = {".github/workflows", ".circleci", ".azure-pipelines"}

CI_PATH_PATTERNS = {
    ".github/workflows",
    ".github\\workflows",
    ".circleci/",
    ".gitlab-ci",
    "azure-pipelines",
}

_overlap = CODE_EXTENSIONS & NON_CODE_EXTENSIONS
if _overlap:
    raise ValueError(
        f"CRITICAL: Extension overlap detected between CODE and NON_CODE: {_overlap}\n"
        f"This indicates a configuration error. Please review extension definitions."
    )

allCodeExts = []

extSets = [
    C_EXTENSIONS,
    CPP_EXTENSIONS,
    PYTHON_EXTENSIONS,
    JAVASCRIPT_EXTENSIONS,
    TYPESCRIPT_EXTENSIONS,
    JSX_EXTENSIONS,
    FRONTEND_FRAMEWORK_EXTENSIONS,
    JAVA_EXTENSIONS,
    KOTLIN_EXTENSIONS,
    SCALA_EXTENSIONS,
    GROOVY_EXTENSIONS,
    CLOJURE_EXTENSIONS,
    CSHARP_EXTENSIONS,
    FSHARP_EXTENSIONS,
    GO_EXTENSIONS,
    RUST_EXTENSIONS,
    SWIFT_EXTENSIONS,
    OBJC_EXTENSIONS,
    UNIX_SHELL_EXTENSIONS,
    WINDOWS_SHELL_EXTENSIONS,
    RUBY_EXTENSIONS,
    PHP_EXTENSIONS,
    PERL_EXTENSIONS,
    LUA_EXTENSIONS,
    R_EXTENSIONS,
    HASKELL_EXTENSIONS,
    OCAML_EXTENSIONS,
    ERLANG_EXTENSIONS,
    ELIXIR_EXTENSIONS,
    ELM_EXTENSIONS,
    DART_EXTENSIONS,
    JULIA_EXTENSIONS,
    NIM_EXTENSIONS,
    CRYSTAL_EXTENSIONS,
    ZIG_EXTENSIONS,
    V_EXTENSIONS,
    VERILOG_EXTENSIONS,
    VHDL_EXTENSIONS,
    ASSEMBLY_EXTENSIONS,
    SOLIDITY_EXTENSIONS,
    MOVE_EXTENSIONS,
    WEB_TEMPLATE_EXTENSIONS,
    SQL_EXTENSIONS,
    GRAPHQL_EXTENSIONS,
    PROTOBUF_EXTENSIONS,
    TERRAFORM_EXTENSIONS,
    SALT_EXTENSIONS,
    JUPYTER_EXTENSIONS,
    PASCAL_EXTENSIONS,
    FORTRAN_EXTENSIONS,
    COBOL_EXTENSIONS,
    ADA_EXTENSIONS,
    D_EXTENSIONS,
    LISP_EXTENSIONS,
    SCHEME_EXTENSIONS,
    VIM_EXTENSIONS,
    TCL_EXTENSIONS,
    AWK_EXTENSIONS,
    SED_EXTENSIONS,
    MAKEFILE_EXTENSIONS,
    CMAKE_EXTENSIONS,
    HACK_EXTENSIONS,
    REASON_EXTENSIONS,
    PURESCRIPT_EXTENSIONS,
]

for extGroup in extSets:
    allCodeExts.extend(extGroup)

if len(allCodeExts) != len(set(allCodeExts)):
    from collections import Counter

    duplicates = [ext for ext, count in Counter(allCodeExts).items() if count > 1]
    raise ValueError(
        f"CRITICAL: Duplicate extensions found in CODE_EXTENSIONS groups: {duplicates}\n"
        f"Each extension should appear in only one group."
    )
