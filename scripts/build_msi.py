"""
Build script for MechCAD-Setup-x64.msi
Generates a genuine Microsoft Windows Installer (.msi) package for MechCAD
using Windows native MSI APIs and cx_Freeze / msilib infrastructure.
"""

import os
import sys
import gc
import re
import shutil
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("build_msi")

# Ensure required imports
try:
    import msilib
    import msilib.schema as schema
    import msilib.sequence as sequence
    from msilib import Binary, CAB, Directory, Feature, add_data, add_tables, gen_uuid, init_database, make_id
    from cx_Freeze.command.bdist_msi import bdist_msi
    from cx_Freeze.command._pydialog import PyDialog
except ImportError as err:
    logger.error("Failed to import required MSI build libraries: %s", err)
    sys.exit(1)


# Package Configuration
PRODUCT_NAME = "MechCAD"
PRODUCT_VERSION = "1.0.0"
MANUFACTURER = "MechCAD Contributors"
PRODUCT_CODE = "{A93E8F4B-6531-4889-BAE8-51CDCA9783D1}"
UPGRADE_CODE = "{5F64E332-9014-4B29-A75D-3EB7A48E085F}"
COMMENTS = "MechCAD - Professional 3D Parametric CAD Modeler with Fusion 360-style workflow"
URL = "https://github.com/mustan5372-tech/MechCAD"


class MechCADMSIBuilder(bdist_msi):
    """Encapsulates UI dialogs and MSI database population."""
    def __init__(self, db, title=f"{PRODUCT_NAME} Setup"):
        self.db = db
        self.title = title
        self.x = 50
        self.y = 50
        self.width = 370
        self.height = 300
        self.modal = 3
        self.modeless = 1
        self.launch_on_finish = False
        self.license_file = None
        self.all_users = True


def build_msi():
    workspace_root = Path(__file__).resolve().parent.parent
    dist_dir = workspace_root / "dist"
    app_dir = dist_dir / "MechCAD"
    output_msi = dist_dir / "MechCAD-Setup-x64.msi"
    icon_path = workspace_root / "assets" / "branding" / "mechcad.ico"

    if not app_dir.exists() or not (app_dir / "MechCAD.exe").exists():
        logger.error("Application directory %s or MechCAD.exe does not exist!", app_dir)
        sys.exit(1)

    if not icon_path.exists():
        logger.error("Icon %s does not exist!", icon_path)
        sys.exit(1)

    logger.info("Target MSI path: %s", output_msi)
    if output_msi.exists():
        try:
            output_msi.unlink()
        except OSError as e:
            logger.warning("Could not unlink existing MSI: %s", e)

    # 1. Initialize MSI Database (64-bit)
    logger.info("Initializing MSI database schema...")
    db = init_database(
        str(output_msi),
        schema,
        PRODUCT_NAME,
        PRODUCT_CODE,
        PRODUCT_VERSION,
        MANUFACTURER,
    )
    add_tables(db, sequence)

    # 2. Add Properties
    logger.info("Configuring installer properties...")
    props = [
        ("DistVersion", PRODUCT_VERSION),
        ("DefaultUIFont", "DlgFont8"),
        ("ErrorDialog", "ErrorDlg"),
        ("Progress1", "Install"),
        ("Progress2", "installs"),
        ("MaintenanceForm_Action", "Repair"),
        ("ALLUSERS", "1"),
        ("ARPNOMODIFY", "1"),
        ("ARPPRODUCTICON", "AppIcon"),
        ("ARPHELPLINK", URL),
        ("ARPURLINFOABOUT", URL),
        ("ARPCOMMENTS", COMMENTS),
        ("UpgradeCode", UPGRADE_CODE.upper()),
        ("SecureCustomProperties", "TARGETDIR;REINSTALLMODE;NEWERVERSIONDETECTED;OLDERVERSIONBEINGREMOVED"),
    ]
    add_data(db, "Property", props)

    # Add Application Icon
    add_data(db, "Icon", [("AppIcon", Binary(str(icon_path)))])

    # 3. Add Custom Actions for Target Directory & Reinstall Mode
    initial_target_dir = rf"[ProgramFiles64Folder]\{PRODUCT_NAME}"
    add_data(
        db,
        "CustomAction",
        [
            ("A_SET_TARGET_DIR", 256 + 51, "TARGETDIR", initial_target_dir),
            ("A_SET_REINSTALL_MODE", 256 + 51, "REINSTALLMODE", "amus"),
        ],
    )
    add_data(
        db,
        "InstallExecuteSequence",
        [
            ("A_SET_TARGET_DIR", 'TARGETDIR=""', 401),
            ("A_SET_REINSTALL_MODE", 'REINSTALLMODE=""', 402),
        ],
    )
    add_data(
        db,
        "InstallUISequence",
        [
            ("PrepareDlg", None, 140),
            ("A_SET_TARGET_DIR", 'TARGETDIR=""', 401),
            ("A_SET_REINSTALL_MODE", 'REINSTALLMODE=""', 402),
            ("SelectDirectoryDlg", "not Installed", 1230),
            ("MaintenanceTypeDlg", "Installed and not Resume and not Preselected", 1250),
            ("ProgressDlg", None, 1280),
        ],
    )

    # 4. Add UI Dialogs
    logger.info("Building installer UI dialogs...")
    builder = MechCADMSIBuilder(db)
    builder.add_ui()

    # 5. Configure Standard Directory Structure
    add_data(
        db,
        "Directory",
        [
            ("DesktopFolder", "TARGETDIR", "."),
            ("ProgramMenuFolder", "TARGETDIR", "."),
            ("MechCADMenuFolder", "ProgramMenuFolder", f"MECHCA~1|{PRODUCT_NAME}"),
        ],
    )

    # 6. Setup Feature and File Packing
    logger.info("Scanning application directory and packing files...")
    cab = CAB("distfiles")
    feature = Feature(
        db,
        "default",
        "Default Feature",
        "MechCAD Core Components",
        1,
        directory="TARGETDIR",
    )
    feature.set_current()

    root = Directory(
        db,
        cab,
        None,
        str(app_dir),
        "TARGETDIR",
        "SourceDir",
    )
    db.Commit()

    # Register main executable component explicitly
    root.start_component(
        component="C_MechCAD_exe",
        feature=feature,
        flags=0,
        keyfile="MechCAD.exe",
    )
    root.add_file("MechCAD.exe")

    # Add Shortcuts referencing the main executable component
    logger.info("Adding Start Menu and Desktop shortcuts...")
    add_data(
        db,
        "Shortcut",
        [
            (
                "SC_Desktop",
                "DesktopFolder",
                "MechCAD",
                "C_MechCAD_exe",
                "[TARGETDIR]MechCAD.exe",
                None,
                COMMENTS,
                None,
                "AppIcon",
                0,
                1,
                "TARGETDIR",
            ),
            (
                "SC_StartMenu",
                "MechCADMenuFolder",
                "MechCAD",
                "C_MechCAD_exe",
                "[TARGETDIR]MechCAD.exe",
                None,
                COMMENTS,
                None,
                "AppIcon",
                0,
                1,
                "TARGETDIR",
            ),
        ],
    )
    # Ensure Start Menu directory is cleaned on uninstall
    add_data(db, "CreateFolder", [("MechCADMenuFolder", "C_MechCAD_exe")])

    # 7. Add File Association (.mcad) via Registry Table
    logger.info("Registering .mcad file extension associations...")
    reg_entries = [
        ("Reg_Ext", -1, r"Software\Classes\.mcad", None, "MechCAD.Document", "C_MechCAD_exe"),
        ("Reg_ProgId", -1, r"Software\Classes\MechCAD.Document", None, "MechCAD 3D Model", "C_MechCAD_exe"),
        ("Reg_Icon", -1, r"Software\Classes\MechCAD.Document\DefaultIcon", None, r'"[TARGETDIR]MechCAD.exe",0', "C_MechCAD_exe"),
        ("Reg_Command", -1, r"Software\Classes\MechCAD.Document\shell\open\command", None, r'"[TARGETDIR]MechCAD.exe" "%1"', "C_MechCAD_exe"),
        ("Reg_App_Name", -1, r"Software\Classes\MechCAD.Document\Application", "ApplicationName", PRODUCT_NAME, "C_MechCAD_exe"),
        ("Reg_App_Company", -1, r"Software\Classes\MechCAD.Document\Application", "ApplicationCompany", MANUFACTURER, "C_MechCAD_exe"),
    ]
    add_data(db, "Registry", reg_entries)

    # 8. Traverse and add remaining files & subdirectories
    file_count = 1  # MechCAD.exe already added
    todo = [root]
    while todo:
        directory = todo.pop()
        for item in sorted(os.listdir(directory.absolute)):
            item_path = os.path.join(directory.absolute, item)
            if item == "MechCAD.exe" and directory.logical == "TARGETDIR":
                continue  # already added
            if os.path.isdir(item_path):
                sfile = directory.make_short(item)
                new_dir = Directory(
                    db,
                    cab,
                    directory,
                    item,
                    item,
                    f"{sfile}|{item}",
                )
                todo.append(new_dir)
            else:
                directory.add_file(item)
                file_count += 1
                if file_count % 100 == 0:
                    logger.info("Added %d files to CAB...", file_count)

    logger.info("Finished adding %d total files. Compressing CAB and committing database...", file_count)
    cab.commit(db)
    db.Commit()

    # Release database handle
    del db
    gc.collect()

    msi_size = output_msi.stat().st_size
    logger.info("SUCCESS! MechCAD-Setup-x64.msi successfully built!")
    logger.info("MSI Path: %s", output_msi)
    logger.info("MSI Size: %d bytes (%.2f MB)", msi_size, msi_size / (1024 * 1024))
    return output_msi


if __name__ == "__main__":
    build_msi()
