import sys
import shutil
import subprocess
import os
import psutil
from PyQt5 import QtWidgets
from ui.mainwindow import Ui_MainWindow   # file UI export từ Qt Designer


# ✅ Lấy đúng thư mục user hiện tại
HOME = os.path.expanduser("~")

# Default Zalo-related folders
FOLDERS = {
    "Zalo":    os.path.join(HOME, "AppData", "Local", "Programs", "Zalo"),
    "ZaloPC":  os.path.join(HOME, "AppData", "Local", "ZaloPC"),
    "ZaloData": os.path.join(HOME, "AppData", "Roaming", "ZaloData"),
}


class ZaloMover(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # Connect buttons
        self.browseButton.clicked.connect(self.choose_folder)
        self.moveButton.clicked.connect(self.move_selected)

        # Reset progress bar
        self.progressBar.setValue(0)

        # Set app title
        self.setWindowTitle("ZaloMove - Developed by Shun")

        # ✅ Disable checkbox nếu folder không tồn tại
        self.check_folders()

    def check_folders(self):
        """Disable checkboxes if default folders don't exist"""
        if not os.path.exists(FOLDERS["Zalo"]):
            self.checkZalo.setEnabled(False)
            self.checkZalo.setText("Zalo (Not Found)")
        if not os.path.exists(FOLDERS["ZaloPC"]):
            self.checkZaloPC.setEnabled(False)
            self.checkZaloPC.setText("ZaloPC (Not Found)")
        if not os.path.exists(FOLDERS["ZaloData"]):
            self.checkZaloData.setEnabled(False)
            self.checkZaloData.setText("ZaloData (Not Found)")

    def choose_folder(self):
        """Open folder chooser dialog"""
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Select New Folder Location")
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
            QtWidgets.QMessageBox.warning(self, "Warning", "Please select a destination folder first.")
            return

        # Nếu Zalo đang chạy → tự kill
        if self.is_zalo_running():
            killed = self.kill_zalo()
            QtWidgets.QMessageBox.information(self, "Info", f"Zalo is closing, please wait {killed}... ")

        # ✅ Always create 'zalo_move' inside the chosen folder
        new_base = os.path.join(user_base, "zalo_move")
        os.makedirs(new_base, exist_ok=True)

        # Determine which folders are checked
        selected = []
        if self.checkZalo.isChecked() and self.checkZalo.isEnabled():
            selected.append("Zalo")
        if self.checkZaloPC.isChecked() and self.checkZaloPC.isEnabled():
            selected.append("ZaloPC")
        if self.checkZaloData.isChecked() and self.checkZaloData.isEnabled():
            selected.append("ZaloData")

        if not selected:
            QtWidgets.QMessageBox.warning(self, "Warning", "Please select at least one valid folder.")
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
                    "Folder Exists",
                    f"{new_path} already exists. Overwrite?",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                    QtWidgets.QMessageBox.No
                )
                if reply == QtWidgets.QMessageBox.No:
                    continue
                shutil.rmtree(new_path, ignore_errors=True)

            if not os.path.exists(old_path):
                errors.append(f"{name} not found at {old_path}")
            else:
                try:
                    # Move folder
                    shutil.move(old_path, new_path)

                    # Create symlink (junction)
                    subprocess.run(f'mklink /J "{old_path}" "{new_path}"',
                                   shell=True, check=True)

                except Exception as e:
                    errors.append(f"Failed to move {name}: {e}")

            # Update progress bar
            self.progressBar.setValue(i)
            QtWidgets.QApplication.processEvents()

        if errors:
            QtWidgets.QMessageBox.critical(self, "Result", "\n".join(errors))
        else:
            QtWidgets.QMessageBox.information(self, "Success", f"Moved: {', '.join(selected)}")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = ZaloMover()
    window.show()
    sys.exit(app.exec_())
