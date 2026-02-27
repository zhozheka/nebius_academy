MAX_PRIORITY = 1000
BASE_PRIORITY = 100
DECAY_PER_DEPTH = 10
MAX_CHARS_PER_FILE = 10_000
MIN_LOC_PER_EXTENSION = 50

DEFAULT_IGNORE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    "bower_components",
    "dist",
    "build",
    "out",
    ".next",
    ".nuxt",
    "target",
    "bin",
    "obj",
    ".venv",
    "venv",
    "__pycache__",
    ".tox",
    "coverage",
    ".pytest_cache",
    ".idea",
    ".vscode",
    "vendor",
}

LOCKFILE_NAMES = {
    "yarn.lock",
    "package-lock.json",
    "pnpm-lock.yaml",
    "composer.lock",
    "Gemfile.lock",
    "Cargo.lock",
    "go.sum",
}

BINARY_EXTS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".bmp",
    ".ico",
    ".pdf",
    ".zip",
    ".tar",
    ".gz",
    ".bz2",
    ".7z",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".mp4",
    ".mov",
    ".mp3",
    ".wav",
}


KEY_FILE_RULES = [
    # 1000: Repo intent / architecture
    (
        1000,
        [
            "README",
            "README.*",
            "docs/index.md",
            "docs/README.md",
            "docs/overview.md",
            "docs/architecture.md",
            "docs/adr/*.md",
            "docs/adr/**/*.md",
            "ARCHITECTURE.*",
            "DESIGN.*",
        ],
    ),
    # 950: Build + dependency manifests (tell you "what it is" quickly)
    (
        950,
        [
            # Node
            "package.json",
            "pnpm-workspace.yaml",
            "lerna.json",
            "nx.json",
            "turbo.json",
            "rush.json",
            "tsconfig.json",
            "tsconfig.*.json",
            # Python
            "pyproject.toml",
            "requirements.txt",
            "requirements-*.txt",
            "requirements/*.txt",
            "Pipfile",
            "setup.py",
            "setup.cfg",
            # JVM
            "pom.xml",
            "build.gradle",
            "build.gradle.kts",
            "settings.gradle",
            "settings.gradle.kts",
            # Other ecosystems
            "go.mod",
            "Cargo.toml",
            "*.sln",
            "*.csproj",
            "Directory.Packages.props",
            "NuGet.config",
            "composer.json",
            "Gemfile",
        ],
    ),
    # 920: Common entrypoints (tell you "what it does" quickly, but can be noisy and less standardized than manifests)
    (
        920,
        [
            # Common root entrypoints
            "main.py",
            "app.py",
            "server.py",
            "__main__.py",
            "manage.py",
            "main.ts",
            "index.ts",
            "server.ts",
            "app.ts",
            "main.js",
            "index.js",
            "server.js",
            "app.js",
            # CLIs
            "cli.py",
            "src/cli.py",
            "bin/*",
            "scripts/*",
        ],
    ),
    # 900: Public interfaces / contracts
    (
        900,
        [
            "*openapi*.yml",
            "*openapi*.yaml",
            "*openapi*.json",
            "*swagger*.yml",
            "*swagger*.yaml",
            "*swagger*.json",
            "schema.graphql",
            "*.graphql",
            "*.proto",
            "*asyncapi*.yml",
            "*asyncapi*.yaml",
            "*asyncapi*.json",
            "*.schema.json",
        ],
    ),
    # 800: CI/CD + release automation (how it builds/tests/deploys)
    (
        800,
        [
            ".github/workflows/*.yml",
            ".github/workflows/*.yaml",
            ".gitlab-ci.yml",
            "azure-pipelines.yml",
            ".circleci/config.yml",
            ".github/dependabot.yml",
            "renovate.json",
            ".pre-commit-config.yaml",
        ],
    ),
    # 750: Deployment/infra/runtime packaging
    (
        750,
        [
            "Dockerfile",
            "docker-compose.yml",
            "docker-compose.*.yml",
            "k8s/*.yml",
            "k8s/*.yaml",
            "manifests/*.yml",
            "manifests/*.yaml",
            "charts/Chart.yaml",
            "charts/*/Chart.yaml",
            "charts/values.yaml",
            "charts/*/values.yaml",
            "*.tf",
            "terragrunt.hcl",
            "serverless.yml",
            "Pulumi.*",
        ],
    ),
    # 700: DB + migrations (what data it owns)
    (
        700,
        [
            "migrations/*",
            "migrations/**/*",
            "prisma/schema.prisma",
            "alembic.ini",
        ],
    ),
    # 650: Policies / contribution (less critical for "what it does", but still useful)
    (
        650,
        [
            "CHANGELOG.*",
            "HISTORY.*",
            "RELEASE_NOTES.*",
            "LICENSE",
            "LICENSE.*",
            "COPYING*",
            "CONTRIBUTING.*",
            "SECURITY.*",
            "CODE_OF_CONDUCT.*",
            "CODEOWNERS",
            ".gitignore",
            ".editorconfig",
        ],
    ),
    # 600: Env templates (sanitize before sending anywhere)
    (
        600,
        [
            ".env.example",
            ".env.template",
        ],
    ),
]
