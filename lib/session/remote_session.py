"""
Dwarf - Copyright (C) 2019 Giovanni Rocca (iGio90)
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>
"""
import frida
from lib.session.session import Session

from ui.device_window import DeviceWindow
from lib import utils


class RemoteSession(Session):

    def __init__(self, app_window):
        super(RemoteSession, self).__init__(app_window)
        self._device_window = DeviceWindow(self._app_window, 'usb')

    @property
    def session_ui_sections(self):
        # what sections we want in session_ui
        return ['hooks', 'bookmarks', 'threads', 'registers', 'debug',
                'console', 'watchers', 'backtrace']

    @property
    def non_closable(self):
        return ['debug', 'ranges', 'modules']

    @property
    def session_type(self):
        """ return session name to show in menus etc
        """
        return 'Remote'

    @property
    def main_menu(self):
        """ return our created menu
        """
        return self._menu

    def stop(self):
        # cleanup ur stuff

        # end session
        super().stop()

    def start(self, args):
        self.dwarf.onScriptDestroyed.connect(self.stop)
        if args.package is None:
            self._device_window.setModal(True)
            self._device_window.onSelectedProcess.connect(self.on_proc_selected)
            self._device_window.onClosed.connect(self._on_devdlg_closed)
            self._device_window.show()
        else:
            self.dwarf.device = frida.get_local_device()
            if not args.spawn:
                print('* Trying to attach to {0}'.format(args.package))
                try:
                    self.dwarf.attach(args.package, args.script, False)
                except Exception as e:  # pylint: disable=broad-except
                    print('-failed-')
                    print('Reason: ' + str(e))
                    print('Help: you can use -sp to force spawn')
                    self.stop()
                    exit(0)
            else:
                print('* Trying to spawn {0}'.format(args.package))
                try:
                    self.dwarf.spawn(args.package, args.script)
                except Exception as e:  # pylint: disable=broad-except
                    print('-failed-')
                    print('Reason: ' + str(e))
                    self.stop()
                    exit(0)

    def on_proc_selected(self, data):
        device, pid = data
        if device:
            self.dwarf.device = device
        if pid:
            try:
                self.dwarf.attach(pid)
            except Exception as e:
                utils.show_message_box('Failed attaching to {0}'.format(pid), str(e))
                self.stop()
                return

    def _on_devdlg_closed(self):
        self.stop()
