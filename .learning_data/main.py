r"""
Local AI Learning Lab - Chapter Selection Launcher
Run from repository root: python .\.learning_data\main.py
"""

import os
import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent

CHAPTERS = [
    {
        "num": 1,
        "title": "Chapter 1 - Basic RAG (completed)",
        "folder": "chapter_01",
        "script": "rag_cli.py",
        "completed": True,
    },
    {
        "num": 2,
        "title": "Chapter 2 - Persistence and Embedding Reuse",
        "folder": "chapter_02",
        "script": "rag_persistent.py",
        "completed": False,
    },
    {
        "num": 3,
        "title": "Chapter 3 - Chunking and Retrieval Evaluation",
        "folder": "chapter_03",
        "script": "evaluate_rag.py",
        "completed": False,
    },
    {
        "num": 4,
        "title": "Chapter 4 - SQLite Fundamentals",
        "folder": "chapter_04",
        "script": "sqlite_app.py",
        "completed": False,
    },
    {
        "num": 5,
        "title": "Chapter 5 - Two Users and Data Isolation",
        "folder": "chapter_05",
        "script": "isolated_rag.py",
        "completed": False,
    },
    {
        "num": 6,
        "title": "Chapter 6 - Local Language Models",
        "folder": "chapter_06",
        "script": "model_wrapper.py",
        "completed": False,
    },
    {
        "num": 7,
        "title": "Chapter 7 - RAG Debugging and Observability",
        "folder": "chapter_07",
        "script": "traced_rag.py",
        "completed": False,
    },
    {
        "num": 8,
        "title": "Chapter 8 - Tools and Tool Calling",
        "folder": "chapter_08",
        "script": "tool_agent.py",
        "completed": False,
    },
    {
        "num": 9,
        "title": "Chapter 9 - Agents and Control Loops",
        "folder": "chapter_09",
        "script": "react_agent.py",
        "completed": False,
    },
    {
        "num": 10,
        "title": "Chapter 10 - Harness Engineering",
        "folder": "chapter_10",
        "script": "test_harness.py",
        "completed": False,
    },
    {
        "num": 11,
        "title": "Chapter 11 - React Integration",
        "folder": "chapter_11",
        "script": "api_server.py",
        "completed": False,
    },
    {
        "num": 12,
        "title": "Chapter 12 - Testing and Hardening",
        "folder": "chapter_12",
        "script": "hardening_suite.py",
        "completed": False,
    },
]


def display_menu():
    print("\n" + "=" * 40)
    print("       LOCAL AI LEARNING LAB")
    print("=" * 40)
    print("\nAvailable chapters:\n")
    for ch in CHAPTERS:
        status_suffix = " (completed)" if ch["completed"] else ""
        title = ch["title"].replace(" (completed)", "")
        print(f"{ch['num']:2d}. {title}{status_suffix}")
    print("\n 0. Exit")
    print("-" * 40)


def run_chapter_1():
    # Chapter 1 runs the preserved rag_cli.py at REPO_ROOT
    script_path = REPO_ROOT / "rag_cli.py"
    if not script_path.exists():
        script_path = BASE_DIR / "chapter_01" / "rag_cli.py"

    if not script_path.exists():
        print(f"\n[ERROR] Could not find Chapter 1 script at: {script_path}")
        return

    print("\n" + "=" * 50)
    print("  LAUNCHING CHAPTER 1: BASIC RAG CLI")
    print(f"  Script: {script_path.name}")
    print("  (Type 'exit' inside the RAG prompt to return here)")
    print("=" * 50 + "\n")

    try:
        # Run in repo root directory so windows_commands.json is resolved
        subprocess.run([sys.executable, str(script_path)], cwd=str(REPO_ROOT), check=False)
    except KeyboardInterrupt:
        print("\n[INFO] Chapter 1 interrupted by user.")
    except Exception as e:
        print(f"\n[ERROR] Failed to run Chapter 1: {e}")

    print("\n[INFO] Returned to Local AI Learning Lab.\n")


def view_chapter_instructions(ch_data):
    ch_num = ch_data["num"]
    folder_name = ch_data["folder"]
    readme_path = BASE_DIR / folder_name / "README.md"
    script_path = BASE_DIR / folder_name / ch_data["script"]

    # Check if user already implemented the chapter script
    if script_path.exists():
        print(f"\n[FOUND] Working implementation detected: {script_path.name}")
        choice = input("Do you want to [R]un the script or [V]iew instructions? (r/v): ").strip().lower()
        if choice == "r":
            print(f"\nLaunching {script_path.name}...")
            try:
                subprocess.run([sys.executable, str(script_path)], cwd=str(script_path.parent), check=False)
            except Exception as e:
                print(f"[ERROR] Failed to execute: {e}")
            return

    print("\n" + "=" * 60)
    print(f"  CHAPTER {ch_num}: {ch_data['title'].replace(f'Chapter {ch_num} - ', '')}")
    print("=" * 60)
    print("\nStatus: Not yet implemented (Self-guided exercise)")
    print(f"Instructions File:\n  {readme_path}\n")

    if not readme_path.exists():
        print(f"[WARNING] Instruction file not found at: {readme_path}")
        return

    while True:
        print("Options:")
        print("  1. Print instructions in terminal")
        print("  2. Open README.md in default editor (Windows)")
        print("  0. Return to main menu")
        sub_choice = input("\nSelect an option (0-2): ").strip()

        if sub_choice == "1":
            print("\n" + "-" * 60)
            try:
                with open(readme_path, "r", encoding="utf-8") as f:
                    print(f.read())
            except Exception as e:
                print(f"[ERROR] Could not read file: {e}")
            print("-" * 60 + "\n")
            break
        elif sub_choice == "2":
            print(f"\nOpening {readme_path}...")
            try:
                os.startfile(str(readme_path))
            except Exception as e:
                print(f"[ERROR] Could not open file via os.startfile: {e}")
                print(f"Path is: {readme_path}")
            break
        elif sub_choice == "0":
            break
        else:
            print("[INVALID] Please choose 0, 1, or 2.")


def main():
    while True:
        display_menu()
        user_input = input("Select a chapter (0-12): ").strip()

        if user_input == "0":
            print("\nExiting Local AI Learning Lab. Happy coding!\n")
            break

        if not user_input.isdigit():
            print("\n[INVALID] Please enter a number between 0 and 12.")
            continue

        selected_num = int(user_input)
        if selected_num < 0 or selected_num > 12:
            print("\n[INVALID] Please enter a number between 0 and 12.")
            continue

        if selected_num == 1:
            run_chapter_1()
        else:
            ch_data = next((c for c in CHAPTERS if c["num"] == selected_num), None)
            if ch_data:
                view_chapter_instructions(ch_data)


if __name__ == "__main__":
    main()
