pyinstaller --name PyChatLLM ^
          --onefile ^
          --windowed ^
          --add-data "settings.json;." ^
          main.py