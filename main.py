from agent.atlas import Atlas


def main():

    atlas = Atlas()

    print("Atlas is ready.")
    print("Type 'exit' to quit.\n")

    while True:

        user_input = input("You: ")

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
