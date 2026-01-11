install:
	uv sync --all-groups

update:
	git reset --hard
	git pull
	uv add picamera
