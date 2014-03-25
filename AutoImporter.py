# coding=utf-8

# Copyright (C) 2014 - Ahmad Dukhan <https://github.com/bhappyz>
import re
import os
import importlib
import pkgutil
import pyclbr

import sublime
import sublime_plugin


IGNORED_PACKAGES = (
    'setuptools',
    'pip',
    'ipython',
    '_',
    'distutils',
)



class PythonAutoImportCommand(sublime_plugin.TextCommand):
    """Locate missing import, give options and import"""

    def run(self, edit, import_point=False, import_str=False):
        self.get_or_build_modules()

        # If these are set we should add the import we already located it
        if import_point and import_str:

            # Check if this is already imported
            occurrence = self.view.find_all(import_str)

            # If not found then we add it
            if not occurrence:
                self.view.insert(edit, import_point, import_str)

            return

        # Get location on the view
        location = self.view.word(self.view.sel()[0].begin())

        # Get the word under the pointer
        name = self.view.substr(location)

        # Lets see if there is a dor before the symbol we are locating
        preceeding_dot = self.view.substr(location.begin()-1) == '.'

        # If nothing is located then you should throw an error
        if not name:
            sublime.message_dialog(
                'The word under the cursor is not an undefined name.')
            return

        # Lets try and figure out where is this import
        self.detect_symbol(edit, name, preceeding_dot)

    def get_or_build_modules(self):
        try:
            if not self.modules:
                self.cache_packages()
        except AttributeError:
            self.modules = {}
            self.cache_packages()

    def is_enabled(self):
        """Determine if this command is enabled or not
        """
        try:
            pointer = self.view.sel()[0].begin()
        except (AttributeError, IndexError):
            return False

        python_source = 'source.python'

        return self.view.match_selector(pointer, python_source)

    def cache_packages(self):
        a = pkgutil.walk_packages(onerror=lambda x: x)

        for module in a:
            module_name = module[1]
            try:
                if not module_name.lower().startswith(IGNORED_PACKAGES):
                    self.modules[module_name] = pyclbr.readmodule_ex(module[1])
            except:
                # Some modules are not importable
                pass

    def detect_symbol(self, edit, name, preceeding_dot=False):
        """ Detects all possible modules for the import using sublime built in symbol lookup"""
        sublime.message_dialog("Ahmad")
        # We need this for later so lets keep it in the instance
        self.import_name = name

        # Get the current active window
        window = sublime.active_window()

        # Lookup the symbol and get all possible imports
        symbols = window.lookup_symbol_in_index(name)

        # Get all the relative path for possible imports
        self.project = [path.replace("/", ".").replace(".py", "") for loc, path, region in symbols]

        self.all_modules = self.project.extend

        # Obviously should throw and error
        if not self.project:
            sublime.message_dialog("Auto import couldn't find symbol in project")
            return

        # Give the user the option
        window.show_quick_panel(self.project, self.insert_import)

    def insert_import(self, index):
        """Gets the appropriate location for the import and calls the current command with params"""
        # Get the insertion line
        iline = self._guess_insertion_line()

        # Get the path of the import
        path = self.results[index]

        # Convert the path into a valid python import
        import_str = self._get_import_from_path(self.import_name, path)

        # Injection points
        current_lines = self.view.lines(sublime.Region(0, self.view.size()))
        import_point = current_lines[iline].begin()

        # Calls it self again with the appropriate params
        self.view.run_command("python_auto_import", {
            "import_point": import_point, "import_str": import_str
        })

    def _get_import_from_path(self, name, module):
        if self.is_method_or_class(name, module):
            import_str = "from {module} import {name}\n\n".format(
                module=module,
                name=name
            )
        else:
            import_str = "import {name}\n\n".format(
                name=name,
            )

        return import_str

    def is_method_or_class(self, name, module):
        try:
            sublime.message_dialog(module)
            if name in dir(importlib.import_module(module)):
                return True
            else:
                return False
        except:
            pass

    def _guess_insertion_line(self):
        view_code = self.view.substr(sublime.Region(0, self.view.size()))
        match = re.search(r'^(@.+|def|class|[A-Za-z0-9_]+\s=)\s+', view_code, re.M)
        if match is not None:
            code = view_code[:match.start()]
            print(code)

        return len(code.split('\n')) - 1

    def _get_symbols_path(self):
        return self.modules
