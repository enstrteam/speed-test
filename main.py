import requests
import time

url = "https://i.pinimg.com/originals/d7/a4/2d/d7a42d6ac095fdf8a24dd4cb11cd753c.jpg?nii=t"


def timer(func):
    def wrapper(*args, **kwargs)   :

        start_time = time.perf_counter()

        result = func(*args, **kwargs)

        end_time = time.perf_counter()

        return result, end_time - start_time
    return wrapper


@timer
def test(url):
    response = requests.get(url)
    return response

def main(url, count = 10):
    total_time = 0
    total_size = 0

    for _ in range(10):
        response, ellapsed_time = test(url)
        total_time += ellapsed_time
        total_size += len(response.content)

    avg_time = total_time / 10

    speed_mb_s = (total_size / 1024 / 1024) / total_time

    print(f"Среднее время: {avg_time:.6f} секунд")
    print(f"Всего скачано: {total_size / 1024 / 1024:.2f} MB")
    print(f"Скорость: {speed_mb_s:.2f} MB/s")


if __name__ == "__main__":
    url = input("Введите URL: ").strip()
    main(url)