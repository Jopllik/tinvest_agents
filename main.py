from agents.supervisor import supervisor
import time
import sys

if __name__ == "__main__":
    print("=== tinvest_agents Local Stage (.exe) ===")
    print("Human confirmation via TG bot. Auto_execute=False for safety.")
    print("Send /stop in TG to shutdown remotely.")
    try:
        while True:
            supervisor.run_full_cycle()
            print("Cycle completed. Waiting 1 hour per rules...")
            time.sleep(3600)  # 1 hour per rules for next scan
    except KeyboardInterrupt:
        print("\nStopped by user (Ctrl+C).")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("System shutdown.")
        sys.exit(0)
