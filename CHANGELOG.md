# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]
- Improved install scripts to check for existing installations of Navidrome and Ollama before installing.
- Added user friendly comments to installation scripts.
- Added CHANGELOG file.
- Added LLM provider support with new `LLM_PROVIDER` setting to switch between OpenAI and Ollama.
- Introduced `LLMClient` abstraction and updated config validation to require either an OpenAI API key or an Ollama model.
- Updated README and environment templates with new instructions.
- Clarified in README that OpenAI or Ollama generate the DJ's responses.
- Updated `scripts/install.sh` to install requirements without the `--user` flag.
- Documented virtual environment setup in the Quick Start guide.
- Changed prerequisite to recommend Python 3.10 or 3.11.

