
def get_openai_key():
    with open("keyfiles/gptkey.txt", "r") as f:
        key = f.read().rstrip()
    return key