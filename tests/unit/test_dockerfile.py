from pathlib import Path

DOCKERFILE = Path(__file__).parents[2] / "Dockerfile"


def test_docker_image_installs_cpu_only_torch_before_app_requirements():
    contents = DOCKERFILE.read_text()

    cpu_index = contents.index("https://download.pytorch.org/whl/cpu")
    requirements_install = contents.index("-r requirements.txt")

    assert cpu_index < requirements_install
    assert "torch==2.7.1" in contents[cpu_index:requirements_install]


def test_app_image_does_not_start_a_second_ollama_server():
    command = next(
        line for line in DOCKERFILE.read_text().splitlines() if line.startswith("CMD ")
    )

    assert "ollama serve" not in command
    assert command.startswith('CMD ["flask", "run"')
