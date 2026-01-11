install:
	uv sync --all-groups

update:
	git reset --hard
	git pull
	# uv add picamera

run-server:
	uv run src/buildmecar/main.py 

test-motors:
	uv run src/buildmecar/test_motors.py
