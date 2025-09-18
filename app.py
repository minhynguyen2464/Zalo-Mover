import sys
import shutil
import subprocess
import os
import psutil
import ctypes
from PyQt5 import QtWidgets
from ui.mainwindow import Ui_MainWindow   # file UI export từ Qt Designer


# ✅ Lấy đúng thư mục user hiện tại
HOME = os.path.expanduser("~")

# Default Zalo-related folders
FOLDERS = {
    "Zalo":    os.path.join(HOME, "AppData", "Local", "Programs", "Zalo"),
    "ZaloPC":  os.path.join(HOME, "AppData", "Local", "ZaloPC"),
    "ZaloData": os.path.join(HOME, "AppData", "Roaming", "ZaloData"),
    "ZaloUpdate":  os.path.join(HOME, "AppData", "Local", "zalo-updater"),   # ✅ mới thêm
}


def get_folder_size(path):
    """Return folder size in MB"""
    total_size = 0
    if not os.path.exists(path):
        return 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            try:
                fp = os.path.join(dirpath, f)
                if os.path.isfile(fp):
                    total_size += os.path.getsize(fp)
            except Exception:
                pass
    return round(total_size / (1024 * 1024), 2)

def is_junction(path):
    """Check if a folder is a junction/symlink in Windows"""
    if not os.path.exists(path):
        return False
    attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
    if attrs == -1:
        return False
    # 0x400 = FILE_ATTRIBUTE_REPARSE_POINT
    return bool(attrs & 0x400)

class ZaloMover(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # Connect buttons
        self.browseButton.clicked.connect(self.choose_folder)
        self.moveButton.clicked.connect(self.move_selected)
        self.deleteButton.clicked.connect(self.delete_old_backups)

        # Reset progress bar
        self.progressBar.setValue(0)

        # Set app title
        self.setWindowTitle("ZaloMove - Phát triển bởi Shun")

        # ✅ Việt hóa label nút
        self.browseButton.setText("Chọn thư mục...")
        self.moveButton.setText("Di chuyển thư mục Zalo")

        # ✅ Disable checkbox nếu folder không tồn tại và show size nếu có
        self.check_folders()

    def check_folders(self):
        """Disable checkboxes if folder không tồn tại hoặc đã là symbolic link"""
        for name, path in FOLDERS.items():
            size = get_folder_size(path)
            label = f"{name} ({size} MB)" if size > 0 else f"{name} (Not Found)"

            disabled = (not os.path.exists(path)) or is_junction(path)

            if name == "Zalo":
                self.checkZalo.setText(label)
                self.checkZalo.setEnabled(not disabled)
            elif name == "ZaloPC":
                self.checkZaloPC.setText(label)
                self.checkZaloPC.setEnabled(not disabled)
            elif name == "ZaloData":
                self.checkZaloData.setText(label)
                self.checkZaloData.setEnabled(not disabled)
            elif name == "ZaloUpdate":   # ✅ xử lý thêm checkbox mới
                self.checkZaloUpdate.setText(label)
                self.checkZaloUpdate.setEnabled(not disabled)

    def choose_folder(self):
        """Open folder chooser dialog"""
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Chọn thư mục đích mới")
        if folder:
            self.newPath.setText(folder)

    def is_zalo_running(self):
        """Check if Zalo is running"""
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] and "Zalo" in proc.info['name']:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False

    def kill_zalo(self):
        """Force kill all Zalo processes"""
        killed = 0
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] and "Zalo" in proc.info['name']:
                    proc.kill()
                    killed += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return killed

    def move_selected(self):
        """Move selected folder(s)"""
        user_base = self.newPath.text().strip()

        if not user_base:
            QtWidgets.QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn thư mục đích trước.")
            return

        # 🔒 Disable nút move để tránh bấm nhiều lần
        self.moveButton.setEnabled(False)
        self.moveButton.setText("Đang xử lý...")

        try:
            # Nếu Zalo đang chạy → tự kill
            if self.is_zalo_running():
                killed = self.kill_zalo()
                QtWidgets.QMessageBox.information(self, "Thông báo", f"Zalo đang bị đóng để di chuyển, nhấn OK để tiếp tục")

            # ✅ Always create 'ZaloMove' inside the chosen folder
            new_base = os.path.join(user_base, "ZaloMove")
            os.makedirs(new_base, exist_ok=True)

            # Determine which folders are checked
            selected = []
            if self.checkZalo.isChecked() and self.checkZalo.isEnabled():
                selected.append("Zalo")
            if self.checkZaloPC.isChecked() and self.checkZaloPC.isEnabled():
                selected.append("ZaloPC")
            if self.checkZaloData.isChecked() and self.checkZaloData.isEnabled():
                selected.append("ZaloData")
            if self.checkZaloUpdate.isChecked() and self.checkZaloUpdate.isEnabled():   # ✅ mới thêm
                selected.append("ZaloUpdate")

            if not selected:
                QtWidgets.QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn ít nhất một thư mục hợp lệ.")
                return

            total = len(selected)
            self.progressBar.setMaximum(total)
            self.progressBar.setValue(0)

            errors = []

            for i, name in enumerate(selected, start=1):
                old_path = FOLDERS[name]
                new_path = os.path.join(new_base, name)

                # Nếu folder đã tồn tại trong zalo_move → hỏi có overwrite không
                if os.path.exists(new_path):
                    reply = QtWidgets.QMessageBox.question(
                        self,
                        "Thư mục đã tồn tại",
                        f"{new_path} đã tồn tại. Bạn có muốn ghi đè không?",
                        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                        QtWidgets.QMessageBox.No
                    )
                    if reply == QtWidgets.QMessageBox.No:
                        continue
                    shutil.rmtree(new_path, ignore_errors=True)

                if not os.path.exists(old_path):
                    errors.append(f"{name} không tìm thấy tại {old_path}")
                else:
                    try:
                        # Tạo bản sao lưu trước khi di chuyển: <folder>.old
                        backup_path = f"{old_path}.old"
                        if os.path.exists(backup_path):
                            reply_backup = QtWidgets.QMessageBox.question(
                                self,
                                "Backup đã tồn tại",
                                f"Đã có bản sao lưu: {backup_path}. Bạn có muốn ghi đè không?",
                                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                QtWidgets.QMessageBox.No
                            )
                            if reply_backup == QtWidgets.QMessageBox.No:
                                # Bỏ qua thư mục này nếu không muốn ghi đè backup
                                continue
                            shutil.rmtree(backup_path, ignore_errors=True)

                        shutil.copytree(old_path, backup_path)

                        # Move folder
                        shutil.move(old_path, new_path)

                        # Create symlink (junction)
                        subprocess.run(f'mklink /J "{old_path}" "{new_path}"',
                                    shell=True, check=True)

                    except Exception as e:
                        errors.append(f"Lỗi khi xử lý {name}: {e}")

                # Update progress bar
                self.progressBar.setValue(i)
                QtWidgets.QApplication.processEvents()

            if errors:
                QtWidgets.QMessageBox.critical(self, "Kết quả", "\n".join(errors))
            else:
                QtWidgets.QMessageBox.information(self, "Thành công", f"Đã di chuyển: {', '.join(selected)}")

        finally:
            # 🔓 Enable lại nút move khi xong
            self.moveButton.setEnabled(True)
            self.moveButton.setText("Di chuyển thư mục Zalo")

    def delete_old_backups(self):
        """Xóa các thư mục backup (*.old) nếu tồn tại"""
        # Tìm tất cả backup tồn tại
        backups = []
        for name, path in FOLDERS.items():
            backup_path = f"{path}.old"
            if os.path.exists(backup_path):
                backups.append((name, backup_path))

        if not backups:
            QtWidgets.QMessageBox.information(self, "Thông báo", "Không tìm thấy thư mục backup (.old) nào để xóa.")
            return

        # Hỏi xác nhận
        backup_list_text = "\n".join([bp for _, bp in backups])
        reply = QtWidgets.QMessageBox.question(
            self,
            "Xác nhận xóa backup",
            f"Bạn có chắc chắn muốn xóa các thư mục backup sau?\n\n{backup_list_text}",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        if reply == QtWidgets.QMessageBox.No:
            return

        errors = []
        deleted = []
        for name, backup_path in backups:
            try:
                shutil.rmtree(backup_path, ignore_errors=False)
                deleted.append(name)
            except Exception as e:
                errors.append(f"Lỗi khi xóa backup {name}: {e}")

        if errors:
            QtWidgets.QMessageBox.critical(self, "Kết quả", "\n".join(errors))
        else:
            QtWidgets.QMessageBox.information(self, "Thành công", f"Đã xóa backup: {', '.join(deleted)}")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = ZaloMover()
    window.show()
    sys.exit(app.exec_())
