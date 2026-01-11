.PHONY: install update run-server test-motors install-service uninstall-service restart-service status-service logs-service

install:
	uv sync --all-groups

update:
	git reset --hard
	git pull

run-server:
	uv run src/buildmecar/main.py 

test-motors:
	uv run src/buildmecar/test_motors.py
	
service-install:
	sudo cp services/buildmecar.service /etc/systemd/system/
	sudo systemctl daemon-reload
	sudo systemctl enable buildmecar
	@echo "Service installed and enabled. Start it with: sudo systemctl start buildmecar"

service-uninstall:
	sudo systemctl stop buildmecar || true
	sudo systemctl disable buildmecar || true
	sudo rm -f /etc/systemd/system/buildmecar.service
	sudo systemctl daemon-reload
	@echo "Service uninstalled"

service-restart:
	sudo systemctl restart buildmecar

status-service:
	sudo systemctl status buildmecar

service-logs:
	sudo journalctl -u buildmecar -f
