import os
import sys

from functools import reduce
from pathlib import Path
from typing import List

from PyQt5.QtCore import QCoreApplication, qDebug
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMessageBox, QWidget

import mobase


class OrphanedScriptExtenderSaveDeleter(mobase.IPluginTool):

    __organizer: mobase.IOrganizer
    __parentWidget: QWidget

    def __init__(self):
        super(OrphanedScriptExtenderSaveDeleter, self).__init__()
        self.__organizer = None
        self.__parentWidget = None

    def init(self, organizer):
        self.__organizer = organizer
        return True

    def name(self):
        return "Orphaned Script Extender Save Deleter"

    def author(self):
        return "AnyOldName3"

    def description(self):
        return self.__tr("Deletes script extender saves which don't have a corresponding base game save.")

    def version(self):
        return mobase.VersionInfo(1, 0, 0, mobase.ReleaseType.final)

    def isActive(self):
        return bool(self.__organizer.managedGame().feature(mobase.ScriptExtender))

    def requirements(self):
        return [
            mobase.PluginRequirementFactory.basic(
                lambda o: bool(o.managedGame().feature(mobase.ScriptExtender)),
                self.__tr("Can only active for game with appropriate script extenders.")
            )
        ]

    def settings(self):
        return []

    def displayName(self):
        return self.__tr("Orphaned Script Extender Save Deleter")

    def tooltip(self):
        return self.__tr("Deletes script extender saves which don't have a corresponding base game save.")

    def icon(self):
        return QIcon()

    def setParentWidget(self, widget):
        self.__parentWidget = widget

    def __listSkseFiles(self, game: mobase.IPluginGame, folder: Path) -> List[Path]:
        if hasattr(game, "savegameSEExtension"):
            ext = game.savegameSEExtension()
        else:
            ext = game.feature(mobase.ScriptExtender).savegameExtension()
        return list(folder.glob("*" + ext))

    def __filesToDelete(self, skseSaves: List[Path], game: mobase.IPluginGame, folder: Path) -> List[Path]:
        # >= MO2 2.4
        files = []
        if not hasattr(game, "listSaves"):
            ext = game.savegameExtension()
            for save in skseSaves:
                if not save.with_suffix("." + ext).is_file():
                    files.append(save)

        else:
            saves = game.listSaves(QDir(folder.as_posix()))
            allfiles = reduce(lambda r, s: r + s.allFiles(), saves, [])
            files = list(set(skseSaves).difference(map(Path, allfiles)))

        return files

    def display(self):
        # Give the user the opportunity to abort
        confirmationButton = QMessageBox.question(
            self.__parentWidget, self.__tr("Before starting deletion..."),
            self.__tr("Please double check that you want your orphaned script extender saves deleted. If you proceed, you won't be able to get them back, even if you find you've copied the corresponding base game save somewhere else so still have a copy."),
            QMessageBox.StandardButtons(QMessageBox.Ok | QMessageBox.Cancel))
        if confirmationButton != QMessageBox.Ok:
            return

        managedGame = self.__organizer.managedGame()
        savesDirectory = Path(managedGame.savesDirectory().absolutePath())
        if self.__organizer.profile().localSavesEnabled():
            savesDirectory = Path(self.__organizer.profile().absolutePath()).joinpath("saves")

        skseSaves = self.__listSkseFiles(managedGame, savesDirectory)
        toDelete = self.__filesToDelete(skseSaves, managedGame, savesDirectory)

        for file in toDelete:
            os.remove(file)

        if not toDelete:
            QMessageBox.information(self.__parentWidget,
                self.__tr("No orphaned script extender saves found"),
                self.__tr("No orphaned script extender co-saves were found, so none were removed."))
        else:
            QMessageBox.information(self.__parentWidget,
                self.__tr("Orphaned script extender saves removed"),
                self.__tr("{0} orphaned script extender co-save(s) removed successfully.").format(len(toDelete)))

    def __tr(self, str):
        return QCoreApplication.translate("OrphanedScriptExtenderSaveDeleter", str)

def createPlugin():
    return OrphanedScriptExtenderSaveDeleter()
