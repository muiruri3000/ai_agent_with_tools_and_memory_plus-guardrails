from threading import Thread

from agent.atlas import Atlas
from monitoring.server import start_metrics_server
from config.settings import METRICS_HOST, METRICS_PORT


def main():

    atlas = Atlas()

    metrics_thread = Thread(
        target=start_metrics_server,
        args=(atlas.metrics,),
        kwargs={
            "host": METRICS_HOST,
            "port": METRICS_PORT,
        },
        daemon=True,
    )

    metrics_thread.start()

    print("Atlas is ready.")
    print("Type 'exit' to quit.\n")

    while True:

        user_input = input("You: ").strip()

        if not user_input:
            continue

        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        try:

            response = atlas.ask(user_input)

            print(f"\nAtlas: {response}\n")

        except Exception as e:

            print("\n❌ ERROR:")
            print(e)
            print()


if __name__ == "__main__":
    main()