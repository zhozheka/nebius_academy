# How to install



# Model selection
I use the model `Qwen/Qwen3-Coder-480B-A35B-Instruct`.
I use only one LLM inference during repository processing, so I need a large context window for better results. This model has a larger context (262K tokens vs 128K for most popular models) and is trained specifically for repo-scale coding and long-context understanding, which is crucial for this task.


# My approach to handling repository contents
I have several features to make a repository profile:
* Name and Owner — the most obvious features; name can say a lot about the project.
* List of the top-level files and directories (with the number of files in each). This helps to understand the structure of the repository.
* Number of files and lines of code by file extension: helps to understand languages and technologies used. To prevent size explosion, the minimum number of lines of code is 50 per extension, and there must be at least 2 files with that extension.
* File content. At first, files are filtered:
    * Binary files are filtered out by extension, then by looking for **b"\x00"** in the file.
    * Lockfiles and some directories (such as **node_modules**, **__pycache__**, **.git**, …) are filtered out using name patterns (see `rules.py`).

* Then a priority value is assigned to each file.
    * First, priority depends on the purpose of the file (from **README** and **docs** to **entrypoints**, **CI/CD** and **policies**) (see `KEY_FILE_RULES` in `rules.py`). For example, **README.md** gets `priority = 1000`, **requirements.txt** gets `priority = 950`, and **Dockerfile** gets `750`.
    * Priority then decreases with increasing depth in the file tree.
    * There is also a constraint on the number of README files (sometimes there are hundreds, and we want to leave room for other files).
* These files are then packed into JSON with the **repository profile** by priority, in order, until they fit the model’s context size. Each file is limited to 10000 characters.
* The **repository profile** with all its features and file contents is passed to the LLM with a system prompt.
* If the **repository profile** does not fit in the context window, it is truncated by removing low-priority files.