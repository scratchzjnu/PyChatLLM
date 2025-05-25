import tkinter as tk
from tkinter import ttk, messagebox
import json
import requests
import os
import sys
from threading import Thread
from functools import partial

class PyChatLLM:
    def __init__(self, root):
        self.root = root
        self.root.title("PyChatLLM V1.0(service@ilester.net)")
        self.root.geometry("800x600")

        # 加载配置
        self.config = self.load_config()

        # 创建界面组件
        self.create_widgets()

    def load_config(self):
        # 动态获取配置路径：打包后使用可执行文件同级目录，未打包使用脚本同级目录
        if getattr(sys, 'frozen', False):
            config_dir = os.path.dirname(sys.executable)
        else:
            config_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(config_dir, "settings.json")
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "api_key": "",
                "model": "Qwen/Qwen2.5-VL-72B-Instruct",
                "max_tokens": 512,
                "temperature": 0.7,
                "top_p": 0.7
            }

    def save_config(self):
        # 动态获取配置路径：打包后使用可执行文件同级目录，未打包使用脚本同级目录
        if getattr(sys, 'frozen', False):
            config_dir = os.path.dirname(sys.executable)
        else:
            config_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(config_dir, "settings.json")
        with open(config_path, "w") as f:
            json.dump(self.config, f, indent=2)

    def create_widgets(self):
        # 对话显示区
        self.chat_text = tk.Text(self.root, state=tk.DISABLED, wrap=tk.WORD)
        self.chat_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # 输入框和按钮框架
        input_frame = ttk.Frame(self.root)
        input_frame.pack(padx=10, pady=10, fill=tk.X)

        # 文本输入框（默认两行高度）
        self.prompt_entry = tk.Text(input_frame, height=2, wrap=tk.WORD)
        self.prompt_entry.pack(side=tk.LEFT, padx=5, fill=tk.BOTH, expand=True)
        
        # 绑定Ctrl+回车发送事件
        self.prompt_entry.bind("<Control-Return>", lambda event: self.send_message())

        self.send_btn = ttk.Button(input_frame, text="发送", command=self.send_message)
        self.send_btn.pack(side=tk.LEFT, padx=5)

        self.settings_btn = ttk.Button(input_frame, text="设置", command=self.open_settings)
        self.settings_btn.pack(side=tk.RIGHT, padx=5)

    def open_settings(self):
        SettingsWindow(self.root, self)

    def send_message(self):
        prompt = self.prompt_entry.get("1.0", tk.END).strip()
        if not prompt:
            messagebox.showwarning("提示", "请输入提示词")
            return

        self.prompt_entry.delete("1.0", tk.END)
        self.send_btn.config(state=tk.DISABLED, text="思考中")
        self.update_chat("你", prompt)

        # 启动线程调用API
        Thread(target=partial(self.call_llm, prompt), daemon=True).start()

    def call_llm(self, prompt):
        url = "https://api.siliconflow.cn/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config['api_key']}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.config['model'],
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.config['max_tokens'],
            "temperature": self.config['temperature'],
            "top_p": self.config['top_p'],
            "stream": False
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=90)
            response.raise_for_status()
            data = response.json()
            if data.get("choices"):
                reply = data["choices"][0].get("message", {}).get("content", "无有效回复")
                self.update_chat("LLM", reply)
            else:
                self.update_chat("错误", "API返回无效数据")
        except Exception as e:
            self.update_chat("错误", f"调用失败: {str(e)}")
        finally:
            self.root.after(0, lambda: self.send_btn.config(state=tk.NORMAL, text="提交"))

    def update_chat(self, role, content):
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.insert(tk.END, f"{role}: {content}\n\n")
        self.chat_text.see(tk.END)
        self.chat_text.config(state=tk.DISABLED)

class SettingsWindow(tk.Toplevel):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.title("设置")
        self.app = app
        self.geometry("400x300")
        self.create_widgets()

    def create_widgets(self):
        # API密钥
        ttk.Label(self, text="API密钥:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.api_entry = ttk.Entry(self, width=40)
        self.api_entry.grid(row=0, column=1, padx=5, pady=5)
        self.api_entry.insert(0, self.app.config["api_key"])

        # 模型
        ttk.Label(self, text="模型:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.model_combo = ttk.Combobox(self, width=40, values=[
            "Qwen/Qwen3-8B",
            "THUDM/GLM-Z1-9B-0414",
            "THUDM/GLM-4-9B-0414",
            "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
            "Qwen/Qwen2.5-7B-Instruct",
            "Qwen/Qwen2.5-Coder-7B-Instruct",
            "internlm/internlm2_5-7b-chat",
            "Qwen/Qwen2-7B-Instruct",
            "THUDM/glm-4-9b-chat"
        ])
        self.model_combo.grid(row=1, column=1, padx=5, pady=5)
        self.model_combo.set(self.app.config["model"])  # 设置当前选中值

        # 最大tokens
        ttk.Label(self, text="最大tokens:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.max_tokens_entry = ttk.Entry(self, width=10)
        self.max_tokens_entry.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        self.max_tokens_entry.insert(0, self.app.config["max_tokens"])

        # 温度
        ttk.Label(self, text="温度(0-1):").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        self.temp_entry = ttk.Entry(self, width=10)
        self.temp_entry.grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)
        self.temp_entry.insert(0, self.app.config["temperature"])

        # 保存按钮
        save_btn = ttk.Button(self, text="保存", command=self.save_settings)
        save_btn.grid(row=4, columnspan=2, pady=10)

    def save_settings(self):
        try:
            self.app.config.update({
                "api_key": self.api_entry.get(),
                "model": self.model_combo.get(),
                "max_tokens": int(self.max_tokens_entry.get()),
                "temperature": float(self.temp_entry.get())
            })
            self.app.save_config()
            messagebox.showinfo("提示", "设置保存成功")
            self.destroy()
        except Exception as e:
            messagebox.showerror("错误", f"输入无效: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PyChatLLM(root)
    root.mainloop()