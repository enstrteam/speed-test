import time
import requests
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.prompt import Prompt
from rich.table import Table

console = Console()

DEFAULT_URL = (
    "https://i.pinimg.com/originals/d7/a4/2d/d7a42d6ac095fdf8a24dd4cb11cd753c.jpg?nii=t"
)


def timer(func):
    """Декоратор для замера времени выполнения функции."""
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        return result, end_time - start_time

    return wrapper


@timer
def download_test(url: str, timeout: int = 15):
    """Выполняет один GET-запрос к указанному URL."""
    response = requests.get(url, timeout=timeout)
    return response


def format_size(num_bytes: int) -> str:
    """Форматирует размер данных в человекочитаемый вид."""
    if num_bytes >= 1024 * 1024:
        return f"{num_bytes / (1024 * 1024):.2f} MB"
    if num_bytes >= 1024:
        return f"{num_bytes / 1024:.1f} KB"
    return f"{num_bytes} B"


def format_speed(speed_mb_s: float) -> str:
    """Форматирует скорость с цветовой подсветкой."""
    if speed_mb_s >= 10.0:
        color = "bold green"
    elif speed_mb_s >= 3.0:
        color = "yellow"
    else:
        color = "red"
    return f"[{color}]{speed_mb_s:.2f} MB/s[/{color}]"


def generate_sparkline(values: list[float]) -> str:
    """Генерирует ASCII-спарклайн динамики значений."""
    if not values:
        return ""
    bars = [" ", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
    min_v = min(values)
    max_v = max(values)
    diff = max_v - min_v

    if diff == 0:
        return "".join(["▅" for _ in values])

    return "".join(bars[int((v - min_v) / diff * (len(bars) - 1))] for v in values)


def run_speed_test(url: str, count: int = 10):
    console.print()
    console.print(
        Panel(
            f"[bold cyan]Тестируемый URL:[/bold cyan] [underline blue]{url}[/underline blue]\n"
            f"[bold cyan]Количество запросов:[/bold cyan] [white]{count}[/white]",
            title="[bold yellow]Параметры теста[/bold yellow]",
            border_style="cyan",
        )
    )
    console.print()

    # Таблица результатов по запросам
    table = Table(
        title="[bold cyan]Детализация запросов[/bold cyan]",
        title_justify="left",
        header_style="bold magenta",
        show_lines=True,
    )
    table.add_column("№", justify="center", style="cyan", width=5)
    table.add_column("Статус", justify="center", width=12)
    table.add_column("Размер", justify="right", width=12)
    table.add_column("Время", justify="right", width=14)
    table.add_column("Скорость", justify="right", width=16)

    speeds: list[float] = []
    durations: list[float] = []
    total_size = 0
    total_time = 0
    successful_runs = 0

    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(complete_style="green", finished_style="bright_green"),
        TaskProgressColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
    )

    with progress:
        task_id = progress.add_task("[bold cyan]Загрузка данных...[/bold cyan]", total=count)

        for i in range(1, count + 1):
            try:
                response, elapsed_time = download_test(url)
                status_code = response.status_code
                size_bytes = len(response.content)

                if status_code == 200:
                    status_text = "[bold green]200 OK[/bold green]"
                    successful_runs += 1
                else:
                    status_text = f"[bold yellow]{status_code}[/bold yellow]"

                speed_mb_s = (size_bytes / (1024 * 1024)) / elapsed_time if elapsed_time > 0 else 0.0

                speeds.append(speed_mb_s)
                durations.append(elapsed_time)
                total_size += size_bytes
                total_time += elapsed_time

                table.add_row(
                    str(i),
                    status_text,
                    format_size(size_bytes),
                    f"{elapsed_time * 1000:.1f} мс" if elapsed_time < 1 else f"{elapsed_time:.3f} с",
                    format_speed(speed_mb_s),
                )

            except requests.RequestException as e:
                table.add_row(
                    str(i),
                    "[bold red]Ошибка[/bold red]",
                    "-",
                    "-",
                    f"[red]{e.__class__.__name__}[/red]",
                )

            progress.advance(task_id)

    # Вывод таблицы с результатами каждого шага
    console.print()
    console.print(table)
    console.print()

    # Итоговые расчеты и вывод сводки
    if successful_runs > 0 and total_time > 0:
        avg_speed = (total_size / (1024 * 1024)) / total_time
        max_speed = max(speeds)
        min_speed = min(speeds)
        avg_latency = (total_time / successful_runs) * 1000
        sparkline = generate_sparkline(speeds)

        summary_text = (
            f"[bold]Успешных запросов:[/bold] [green]{successful_runs}/{count}[/green]\n"
            f"[bold]Всего скачано:[/bold]     [cyan]{format_size(total_size)}[/cyan]\n"
            f"[bold]Общее время:[/bold]       [cyan]{total_time:.2f} сек[/cyan]\n"
            f"[bold]Средняя задержка:[/bold]  [cyan]{avg_latency:.1f} мс[/cyan]\n"
            f"────────────────────────────────────────\n"
            f"[bold]Средняя скорость:[/bold]  {format_speed(avg_speed)}\n"
            f"[bold]Пиковая скорость:[/bold]  {format_speed(max_speed)}\n"
            f"[bold]Мин. скорость:[/bold]     {format_speed(min_speed)}\n"
            f"[bold]График динамики:[/bold]   [bold magenta]{sparkline}[/bold magenta] [dim](мин -> макс)[/dim]"
        )

        console.print(
            Panel(
                summary_text,
                title="[bold green]📊 Итоговая статистика[/bold green]",
                border_style="green",
                padding=(1, 2),
            )
        )
    else:
        console.print(
            Panel(
                "[bold red]Не удалось успешно выполнить ни одного запроса.[/bold red]",
                title="[bold red]Ошибка[/bold red]",
                border_style="red",
            )
        )


def main():
    console.print(
        Panel.fit(
            "[bold cyan]⚡ Network Speed Tester[/bold cyan]\n"
            "[dim]Утилита для измерения и визуализации скорости сетевой загрузки[/dim]",
            border_style="cyan",
            padding=(1, 4),
        )
    )

    try:
        user_url = Prompt.ask(
            "[bold yellow]Введите URL для теста[/bold yellow]",
            default=DEFAULT_URL,
        ).strip()

        count_input = Prompt.ask(
            "[bold yellow]Количество запросов[/bold yellow]",
            default="10",
        ).strip()

        count = int(count_input) if count_input.isdigit() and int(count_input) > 0 else 10

        run_speed_test(user_url, count)

    except KeyboardInterrupt:
        console.print("\n[bold red]Тестирование прервано пользователем.[/bold red]")


if __name__ == "__main__":
    main()