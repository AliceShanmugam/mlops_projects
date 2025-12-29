from prefect import flow, task
import time


@task(retries=3, retry_delay_seconds=5)
def say_hello(name):
    time.sleep(1)
    return f"Hello {name}!"


@flow(name="Hello Flow")
def hello_world(name: str = "World"):
    result = say_hello(name)
    print(result)
    return result


if __name__ == "__main__":
    hello_world()
