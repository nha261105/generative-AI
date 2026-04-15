
# SHOW LIST COMMAND
list:
	@echo ""
	@echo "make install -> cài đặt toàn bộ (hơi nặng nên ko recommend tải tutu thoi)"
	@echo "make venv -> tạo môi trường ảo"
	@echo "make depen -> cài denpendency cần thiết"
	@echo "make ollama -> cài ollama"
	@echo "make qwen -> pull model qwen2.5:7b"
	@echo "make run -> chạy app = streamlit"
	@echo "make clean -> xóa venv"
	@echo ""

# INSTALL 1 Lần
install: venv depen ollama qwen

# Tạo VENV
venv:
	python3 -m venv venv

# Cài Depen
depen:
	./venv/bin/pip install --upgrade pip
	./venv/bin/pip install -r requirements.txt

# Cài ollama
ollama:
	curl -fsSL https://ollama.com/install.sh | sh

# Pull model
qwen:
	ollama pull qwen2.5:7b

# Chạy app
run:
	@if ! pgrep -x ollama >/dev/null; then \
		echo "Starting Ollama..."; \
		ollama serve >/tmp/ollama.log 2>&1 & \
		sleep 2; \
	else \
		echo "Ollama already running, skip start."; \
	fi
	STREAMLIT_SERVER_FILE_WATCHER_TYPE=none ./venv/bin/streamlit run app.py

# Xóa venv
clean:
	rm -rf venv