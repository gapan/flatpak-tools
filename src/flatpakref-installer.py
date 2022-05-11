#!/usr/bin/python3
# vim:et:sta:sts=4:sw=4:ts=8:tw=79:

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Vte', '2.91')
from gi.repository import Gtk, GLib, Pango, Vte
import subprocess
import sys
import os

# Internationalization
import locale
import gettext
locale.setlocale(locale.LC_ALL, '')
locale.bindtextdomain("flatpakref-installer", "/usr/share/locale")
gettext.bindtextdomain("flatpakref-installer", "/usr/share/locale")
gettext.textdomain("flatpakref-installer")
_ = gettext.gettext

def print_help():
    print(_("USAGE:") + " flatpakref-installer file.flatpakref")

def mimetype_is_flatpakref(filename):
    args = ['/usr/bin/xdg-mime', 'query', 'filetype', filename]
    process = subprocess.Popen(args, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
    output = process.communicate()[0].decode('utf8').strip()
    status = process.returncode
    if status == 0 and output == 'application/vnd.flatpak.ref':
        return True
    return False

def check_args(args):
    if len(args) != 2 or not args[1].endswith('.flatpakref'):
        print(_("ERROR:") + " " + _("invalid arguments"))
        print()
        print_help()
        sys.exit(1)

def flatpak_search(app_id, remote):
    args = ['/usr/bin/flatpak', 'search',
        '--columns=name:f,description:f,application:f,version:f,remotes:f',
        app_id]
    process = subprocess.Popen(args, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
    output = process.communicate()[0].decode('utf8').splitlines()
    status = process.returncode
    d = None
    found = False
    if status == 0:
        for line in output:
            line = line.strip()
            try:
                name, description, res_app_id, version, res_remote = line.split('\t')
                found = True
            except ValueError:
                found = False
        if found and res_app_id == app_id and res_remote == remote:
            d = {'name': name,
                 'remote': remote,
                 'app_id': app_id,
                 'description': description,
                 'version': version}
            return True, d
    return False, d

def flatpakref_is_valid(flatpakref_file):
    if not mimetype_is_flatpakref(flatpakref_file):
        return False, None, None
    section_ok = False
    app_id = None
    remote = None
    with open(flatpakref_file) as f:
        contents = f.readlines()
        for line in contents:
            line = line.strip()
            if line == '' or line.startswith('#'):
                pass
            elif line == '[Flatpak Ref]':
                section_ok = True
            if section_ok:
                if line.startswith('Name='):
                    app_id = line.partition('=')[2]
                elif line.startswith('SuggestRemoteName='):
                    remote = line.partition('=')[2]
    if not section_ok or app_id == None or remote == None:
        return False, None, None
    return True, app_id, remote

class FlatpakrefInstaller:

    #
    # Main window signals
    #
    def on_button_install_clicked(self, widget, data=None):
        self.vte_term = Vte.Terminal()
        self.box_vte.add(self.vte_term)
        self.vte_term.set_sensitive(False)
        self.vte_term.set_size(80, 25)
        self.vte_term.set_font(Pango.FontDescription('Monospace 12'))
        self.vte_term.connect('child-exited', self.on_vte_child_exited_cb)
        self.vte_term.show()
        self.window_install.show()
        args = ['/usr/bin/flatpak', 'install', '-y',
            self.flatpak_details['remote'], self.flatpak_details['app_id']]
        self.vte_term.spawn_async(
            Vte.PtyFlags.DEFAULT, # Pty Flags
            os.environ['HOME'], # Working DIR
            args, # Command/BIN (argv)
            None, # Environmental Variables (envv)
            GLib.SpawnFlags.DEFAULT, # Spawn Flags
            None, None, # Child Setup
            GLib.MAXINT, # Timeout (-1 for indefinitely)
            None, # Cancellable
            None, # Callback
            None # User Data
        )

    def on_button_cancel_clicked(self, widget, data=None):
        self.gtk_main_quit()

    def on_button_about_clicked(self, widget, data=None):
        self.window_about.show()

    def gtk_main_quit(self):
        Gtk.main_quit()

    #
    # About dialog signals
    #
    def on_window_about_response(self, widget, data=None):
        self.window_about.hide()

    def on_window_about_delete_event(self, widget, event):
        self.window_about.hide()
        return True

    #
    # Error window signals
    #
    def on_button_error_exit_clicked(self, widget, data=None):
        self.gtk_main_quit()

    #
    # Installation window signals
    #
    def on_button_install_cancel_clicked(self, widget, data=None):
        self.installation_cancelled_by_user = True
        self.box_vte.remove(self.vte_term)
        self.window_install.hide()
        self.vte_term.destroy()

    def on_vte_child_exited_cb(self, terminal, status=None):
        self.box_vte.remove(self.vte_term)
        self.window_main.hide()
        self.window_install.hide()
        self.vte_term.destroy()
        # for some reason the child exit status is times 256 the actual one
        if status == 0:
            self.gtk_main_quit()
        else:
            if self.installation_cancelled_by_user:
                self.gtk_main_quit()
            else:
                self.label_error.set_text(
                    _("There was an error while installing the Flatpak.") + \
                            " " + _("Installation cannot be completed.") + \
                            "\n\n" + _("Error code: ") + str(status))
                self.window_error.show()


    def __init__(self, flatpakref_file):
        builder = Gtk.Builder()
        builder.set_translation_domain("flatpakref-installer")
        if os.path.exists('flatpakref-installer.ui'):
            builder.add_from_file('flatpakref-installer.ui')
        elif os.path.exists('/usr/share/flatpak-tools/flatpakref-installer/flatpakref-installer.ui'):
            builder.add_from_file(
                '/usr/share/flatpak-tools/flatpakref-installer/flatpakref-installer.ui')
        self.window_main = builder.get_object('window_main')

        self.label_name = builder.get_object('label_name')
        self.label_description = builder.get_object('label_description')
        self.label_app_id = builder.get_object('label_app_id')
        self.label_version = builder.get_object('label_version')

        self.window_about=builder.get_object('window_about')

        self.window_error = builder.get_object('window_error')
        self.label_error = builder.get_object('label_error')

        self.window_install = builder.get_object('window_install')
        self.box_vte = builder.get_object('box_vte')
        self.installation_cancelled_by_user = False

        builder.connect_signals(self)

        valid, app_id, remote = flatpakref_is_valid(flatpakref_file)
        found = False
        if valid:
            found, self.flatpak_details = flatpak_search(app_id, remote)
        else:
            self.label_error.set_text(
                _("The Flatpak reference file is not valid.") + \
                        " " + _("Installation cannot be completed."))
            self.window_error.show()
        if found:
            self.label_name.set_text(self.flatpak_details['name'])
            self.label_description.set_text(self.flatpak_details['description'])
            self.label_app_id.set_text(app_id)
            self.label_version.set_text(self.flatpak_details['version'])
        else:
            self.label_error.set_text(
                _("Flatpak not found.") + \
                        " " + _("Installation cannot be completed."))
            self.window_error.show()


if __name__ == "__main__":
    check_args(sys.argv)
    app = FlatpakrefInstaller(sys.argv[1])
    app.window_main.show()
    Gtk.main()
