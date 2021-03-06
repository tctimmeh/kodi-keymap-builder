#!/usr/bin/env python3
import argparse
import csv
from xml.dom import minidom

import copy


class LircInput(object):
    OBC_NUMBER = 0

    def __init__(self, **data):
        self.function = data.pop('function')
        self.physical = data.pop('physical')
        self.lirc_name = data.pop('lirc name', None)
        self.key = data.pop('key', None)
        self.reserved = data.pop('reserved')
        self.global_action = data.pop('global')
        self.other_actions = copy.copy(data)
        self.obc = LircInput.get_obc()

    @classmethod
    def get_obc(cls):
        cls.OBC_NUMBER += 1
        return cls.OBC_NUMBER


class KeymapBuilderApp(object):
    NON_WINDOW_COLUMNS = ['function', 'physical', 'lirc name', 'key', 'reserved', 'global']

    def __init__(self):
        self.input_file = ''
        self.inputs = []
        self.window_names = []

        self.parse_command_line()
        self.read_input()
        self.create_lirc_map()
        self.create_keymap()

    def parse_command_line(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('input_file')
        args = parser.parse_args()
        self.input_file = args.input_file

    def read_input(self):
        with open(self.input_file) as csv_file:
            input_reader = csv.DictReader(csv_file)

            self.window_names = copy.copy(input_reader.fieldnames)
            for column_name in self.NON_WINDOW_COLUMNS:
                try:
                    self.window_names.remove(column_name)
                except ValueError:
                    pass

            self.inputs = [LircInput(**row) for row in input_reader]

    def create_lirc_map(self):
        doc = minidom.Document()
        root = doc.createElement('lircmap')
        doc.appendChild(root)

        remote = doc.createElement('remote')
        remote.setAttribute('device', 'mceusb')
        root.appendChild(remote)

        for input in self.inputs:
            if input.lirc_name is None:
              continue

            e = doc.createElement('obc{}'.format(input.obc))
            text = doc.createTextNode(input.lirc_name)
            e.appendChild(text)
            remote.appendChild(e)

        with open('Lircmap.xml', 'w') as output_file:
            output_file.write(doc.toprettyxml())

    def create_keymap(self):
        doc = minidom.Document()
        root = doc.createElement('keymap')
        doc.appendChild(root)

        global_element = doc.createElement('global')
        root.appendChild(global_element)

        global_remote = doc.createElement('universalremote')
        global_element.appendChild(global_remote)

        global_keyboard = doc.createElement('keyboard')
        global_element.appendChild(global_keyboard)

        window_remote_elements = {}
        window_keyboard_elements = {}
        for window_name in self.window_names:
            window_element = doc.createElement(window_name)
            root.appendChild(window_element)

            remote_element = doc.createElement('universalremote')
            window_element.appendChild(remote_element)

            keyboard_element = doc.createElement('keyboard')
            window_element.appendChild(keyboard_element)

            window_remote_elements[window_name] = remote_element
            window_keyboard_elements[window_name] = keyboard_element

        for input in self.inputs:
            if input.lirc_name:
                if input.global_action:
                    global_action = doc.createTextNode(input.global_action)
                else:
                    global_action = doc.createTextNode('noop')

                global_input = doc.createElement('obc{}'.format(input.obc))
                global_input.appendChild(global_action)
                global_remote.appendChild(global_input)

            if input.key and not input.reserved:
                if input.global_action:
                    global_action = doc.createTextNode(input.global_action)
                else:
                    global_action = doc.createTextNode('noop')

                global_input = doc.createElement(input.key)
                global_input.appendChild(global_action)
                global_keyboard.appendChild(global_input)

            for window_name, action in input.other_actions.items():
                if not action:
                    continue

                if input.lirc_name:
                    window_element = window_remote_elements[window_name]
                    action_text = doc.createTextNode(action)
                    action_element = doc.createElement('obc{}'.format(input.obc))
                    action_element.appendChild(action_text)
                    window_element.appendChild(action_element)

                if input.key:
                    window_element = window_keyboard_elements[window_name]
                    action_text = doc.createTextNode(action)
                    action_element = doc.createElement(input.key)
                    action_element.appendChild(action_text)
                    window_element.appendChild(action_element)

        with open('keymap.xml', 'w') as output_file:
            output_file.write(doc.toprettyxml())


if __name__ == '__main__':
    KeymapBuilderApp()
