.PHONY: setup all clean verify
setup:
	./setup_wsl.sh
all:
	./run_all.sh
verify:
	. .venv/bin/activate && python src/validate_reproduction.py --heatwave-out outputs/generated/heatwaves --tmax-out outputs/generated/tmax
clean:
	rm -rf outputs/generated
