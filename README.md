# 📦 Zalo Mover

A simple PyQt5 app that helps you move **Zalo, ZaloPC, and ZaloData** folders from `C:\` drive to another location (e.g., `D:\`) and automatically creates symbolic links (junctions).  
This helps **free up space on C drive** without breaking Zalo.

---

## 🚀 Features

- GUI built with **PyQt5**
- Select which folders to move (`Zalo`, `ZaloPC`, `ZaloData`)
- Auto-create symbolic links (`mklink /J`)
- Auto-kill running Zalo before moving
- Progress bar for status
- Disable checkboxes if folder does not exist
- Friendly status messages

---

## 🛠 Requirements

- Python 3.8+
- Windows (tested on Windows 10/11)
- Administrator privilege (required for `mklink`)

Install dependencies:

```bash
pip install -r requirements.txt
```
