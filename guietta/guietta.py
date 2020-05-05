# -*- coding: utf-8 -*-

import functools
from collections import Iterable

from PyQt5.QtWidgets import QApplication, QLabel, QWidget
from PyQt5.QtWidgets import QPushButton, QRadioButton, QCheckBox
from PyQt5.QtWidgets import QLineEdit, QGridLayout


if QApplication.instance() is None:
    app = QApplication([])


# Widget shortcuts

B = QPushButton
E = QLineEdit
_ = QLabel
C = QCheckBox
R = QRadioButton

class ___:   # Horizontal continuation
    pass

class I:     # Vertical continuation
    pass

_specials = (_, ___, I)

_default_signals = {QPushButton: 'clicked',
                    QLineEdit: 'returnPressed'}

# Compact element processing

def _compact_label(x):
    if isinstance(x, str) and not x.startswith('__'):
        return QLabel(x)
    else:
        return x

def _compact_button(x):
    if _iterable(x) and isinstance(x[0], str):
        return QPushButton(x[0])
    else:
        return x

def _compact_lineedit(x):
    if isinstance(x, str) and x.startswith('__') and x.endswith('__'):
        return QLineEdit(x)
    else:
        return x

_compacts = [_compact_label, 
             _compact_button,
             _compact_lineedit]

def _convert_compat_to_widget(x):
    for func in _compacts:
        x = func(x)
    return x

# Some helper functions


def _iterable(x):
    return isinstance(x, Iterable) and not isinstance(x, str)


def _normalize(x):
    return ''.join(c for c in x if c.isalnum() or c == '_')


def _bound_method(method):
    return hasattr(method, '__self__')

def _filter_lol(lol, func):
    for row in lol:
        for i in range(len(row)):
            row[i] = func(row[i])

def _check_widget(x):
    if not isinstance(x, QWidget) and x not in _specials:
        raise ValueError('Element %s is not a widget' % x)
    return x

def _check_callable(x):
    if not callable(x) and x not in _specials:
        raise ValueError('Element %s is not callable' % x)
    return x

def _check_string(x):
    if not isinstance(x, str) and x not in _specials:
        raise ValueError('Element %s is not a string' % x)
    return x


def _layer_check(lol):
    '''
    Argument checking for layers.

    Checks that the arguments to a layer (__init__, events(), colors(), etc)
    are well-formed: a series of lists of equal lengths.
    and with valid elements. In case on any error, an exception
    will be raised.

    Parameters
    ----------
    *lists : any
        the arguments to check

    Raises
    ------
    ValueError
        In case the arugments are not lists or the lengths differ
    '''
    ncols = len(lol[0])
    for row in lol:
        if not _iterable(row):
            raise ValueError('Arguments are not lists (or iterables)')

        if len(row) != ncols:
            raise ValueError('Row lengths differ')


class Gui:
    '''Main GUI object.

    The GUI is defined passing to the initializer a set of QT widgets
    organized in rows of equal length. All other method that expect
    lists (like events() or names()) will expect a series of list with
    the same length.

    Every widget will be added as an attribute to this instance,
    using the widget text as the attribute name (removing all special
    characters and only keeping letters, numbers and underscores.)
    '''

    def __init__(self, *lists):

        # Input argument checks
        def must_be_widget(x):
            return isinstance(x, QWidget) or x in _specials
        _layer_check(lists)
        _filter_lol(lists, _convert_compat_to_widget)
        _filter_lol(lists, _check_widget)

        self._layout = QGridLayout()
        self._widgets = {}    # widgets by name
        self._aliases = {}    # name aliases (1 alias per name)

        # Intermediate step that will be filled by replicating
        # widgets when ___ and I are encountered.
        self._step1 = [[None] * len(lists[0]) for i in range(len(lists))]

        for i, row in enumerate(lists):
            for j, element in enumerate(row):
                # Special cases. ___ and 'I' will replicate
                # the widgets from the previous column and row.
                if element == _:
                    element = QLabel('')
                elif element == ___:
                    self._step1[i][j] = self._step1[i][j-1]
                    continue
                elif element == I:
                    self._step1[i][j] = self._step1[i-1][j]
                    continue

                self._step1[i][j] = element

        # Now a multi-cell widget has been replicated both in rows
        # and in columns. Look for repetitions to calculate spans.

        done = set()  # To avoid repeated insertions
        for i, row in enumerate(lists):
            for j, element in enumerate(row):

                element = self._step1[i][j]
                if element not in done:
                    rowspan = 0
                    colspan = 0
                    for ii in range(i, len(lists)):
                        if self._step1[ii][j] == element:
                            rowspan += 1
                    for jj in range(j, len(row)):
                        if self._step1[i][jj] == element:
                            colspan += 1

                    self._layout.addWidget(element, i, j, rowspan, colspan)
                    text = _normalize(element.text())
                    while text in self._widgets:
                        text += '_'
                    self._widgets[text] = element
                    done.add(element)

    def events(self, *lists):
        '''Defines the GUI events

        The argument must be a layout with the same shape as the
        initializer. Every element is the callback function to be
        called when the default signal of the widget is fired.
        
        Bound methods are called without arguments. Functions and
        unbound methods will get a single argument with a reference
        to this Gui instance.
        '''
        # Input argument checks
        def must_be_callable(x):
            return callable(x) or x in _specials
        _layer_check(lists)
        _filter_lol(lists, _check_callable)

        for i, row in enumerate(lists):
            for j, slot in enumerate(row):

                if slot not in _specials:
                    item = self[i,j]
                    signal = getattr(item, _default_signals[item.__class__])
                    if _bound_method(slot):
                        signal.connect(slot)
                    else:
                        f = functools.partial(slot, self)
                        signal.connect(functools.partial(slot, self))

    def names(self, *lists):
        '''Overrides the default widget names
        
        The argument must be a layout with she same shape as the
        initializer. Every element is a string with a name alias
        for the widget in that position.
        '''
        _layer_check(lists)
        _filter_lol(lists, _check_string)

        names_by_widget = {v: k for k, v in self._widgets.items()}

        for i, row in enumerate(lists):
            for j, alias in enumerate(row):

                if alias not in _specials:
                    item = self[i,j]
                    name = names_by_widget[item]
                    self._aliases[alias] = name

    def colors(self, *args):
        '''Defines the GUI colors'''
        pass

    def groups(self, *args):
        '''Defines the GUI widget groups'''
        pass

    def __getattr__(self, name):
        '''Returns a widget using its name or alias'''

        if name in self._aliases:
            name = self._aliases[name]

        if name in self._widgets:
            return self._widgets[name]
        else:
            # Default behaviour
            raise AttributeError

    def __getitem__(self, name):
        '''Widget by coordinates [row,col]'''
        return self._layout.itemAtPosition(name[0], name[1]).widget()

    def all(group=''):
        '''Replicates command on all widgets'''
        pass

    def layout(self):
        '''Returns the Gui layout, containing all the widgets'''
        return self._layout

    def window(self):
        '''Builds a QT window containin all the Gui widgets and returns it'''

        window = QWidget()
        window.setLayout(self._layout)
        return window

    def import_into(self, obj):
        '''
        Widget importer

        Adds all this Gui's widget to `obj` as new attributes. Aliases
        defind with names() are also added.
        '''
        widgets = {**self._widgets, **self._aliases}

        for name, widget in widgets.items():
            if hasattr(obj, name):
                raise Exception('Cannot import: duplicate name %s ' % name)
            else:
                setattr(obj, name, widget)
        
    def run(self, argv=None):
        '''Display the Gui and start the event loop'''

        if argv is None:
            argv = []
        app = QApplication.instance()
        window = self.window()
        window.show()
        app.exec_()

# ___oOo___
