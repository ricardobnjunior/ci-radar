from agents import make_ci_agent
from orchestrator import run_ci

def main():

    agent = make_ci_agent()
    out = run_ci(agent)

    print("\n=== DIGEST ===\n")
    print(out)

if __name__ == "__main__":
    main()
