import pathlib
import requests


def download(url: str, destination: pathlib.Path) -> None:
	response = requests.get(url, timeout=60)
	response.raise_for_status()
	destination.write_bytes(response.content)


if __name__ == "__main__":
	asset_url = (
		"https://raw.githubusercontent.com/Elthen-/Pixel-Art-Animations/master/"
		"Fighter%20Pack/Blue/Idle.png"
	)
	target_path = pathlib.Path(__file__).with_name("test_idle.png")
	download(asset_url, target_path)
	print(f"Downloaded {target_path.name} -> {target_path.stat().st_size} bytes")
