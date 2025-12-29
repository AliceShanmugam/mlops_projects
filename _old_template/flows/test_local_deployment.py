from prefect import flow, task


@task
def say_hello():
    print("Hello World!")


@flow(name="Hello Flow")
def hello_flow():
    say_hello()


if __name__ == "__main__":
    hello_flow()