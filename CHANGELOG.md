# Changelog

All notable changes to this project will be documented in this file.  
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)  
and this project adheres to [Semantic Versioning](https://semver.org/).

---

## [1.0.0] - 2025-09-12

### Added

- First public release of **Zalo Mover** 🚀
- Support moving 3 default Zalo folders:
  - `Zalo`
  - `ZaloPC`
  - `ZaloData`
- Automatically create **junction (symbolic link)** from default path → new location
- Automatic creation of `zalo_move` subfolder at target location
- UI with:
  - Checkbox selection for folders
  - Destination folder browser
  - Progress bar
- Automatic cleanup: delete old folder after move to free C: drive
- Success popup with freed space info

---

## [1.0.3] - 2025-09-15

### Added

- Change the app language to Vietnamese

---

## [Unreleased]

### Planned

- Add **auto-update checker**
- Add **multi-language UI (EN + VN)**
- Add **logging system** to help troubleshooting
- Create **portable version** (no installer required)
