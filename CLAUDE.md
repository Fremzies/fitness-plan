# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

<!-- Add build, lint, test, and run commands here as the project takes shape. -->

## Architecture

<!-- Add high-level architecture notes here once the codebase grows. -->

## Terminal Usage

This project involves terminal-based operations. Key conventions:

- Use `run_in_terminal` for executing shell commands
- Prefer synchronous mode for one-shot commands, async for long-running processes
- Always validate command output and handle errors appropriately
- Use absolute paths for file operations to avoid ambiguity
- Chain commands with `&&` for simple sequences, pipelines `|` for data flow
