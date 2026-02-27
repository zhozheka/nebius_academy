# How to install



# Model selection
I use model `Qwen/Qwen3-Coder-480B-A35B-Instruct`.
I use only one LLM inference during the repository processing, so I need a large context window to get a better result. This model has a larger context with (262K tokens vs 128K for most of the popular models). Also, this model is trained specifically for repo-scale coding and long-context understanding which is crusial in the task.


# My approach to handling repository contents
