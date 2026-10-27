import time
import sys
import os
import msvcrt

if __name__ == "__main__":
    # Большое приветствие по центру в самом начале (одна надпись, увеличенный шрифт имитацией отступами и рамкой)
    width = 80
    greeting = "BotJopTorgoval приветствует тебя!"
    question = "Начнем работу? (Enter - да / Esc - нет)"
    print("\n" * 3)
    print(" " * 5 + "=" * 70)
    print(" " * 5 + greeting.center(70))
    print(" " * 5 + "=" * 70)
    print("\n" + " " * 5 + question.center(70) + "\n")
    print("Нажмите Enter или Esc...")
    while True:
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key == b'\r':  # Enter
                print("Да, начинаем работу системы...")
                break
            elif key == b'\x1b':  # Esc
                print("Работа отменена, закрываю консоль...")
                sys.exit(0)
    from agents.supervisor import supervisor
    print("\n=== tinvest_agents Local Stage (.exe) ===")
    print("Human confirmation via TG bot. Auto_execute=False for safety.")
    print("Send /stop in TG to shutdown remotely.\n")
    try:
        while True:
            supervisor.run_full_cycle()
            print("Cycle completed. Waiting 1 hour per rules...")
            time.sleep(3600)
    except KeyboardInterrupt:
        print("\nStopped by user (Ctrl+C).")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("System shutdown.")
        input("Press Enter to close console...")
        sys.exit(0)
