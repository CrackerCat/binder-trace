import hexdump
import pyperclip

from prompt_toolkit.filters import Condition
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import AnyContainer, FormattedTextControl, HSplit, Window
from prompt_toolkit.widgets import Label

from binder_trace.tui import listing
from binder_trace.tui.selection import SelectionViewList
from binder_trace.tui.widget.frame import SelectableFrame


class StructureFrame:

    def __init__(self, transactions: SelectionViewList, max_height: int) -> None:
        self.transactions = transactions
        self.transactions.on_selection_change += self.update_content

        # The SVL has one less than max height to allow for banner at the top
        self.field_selection = SelectionViewList([], max_view_size=max_height - 1)

        self.max_height = max_height

        self.container = SelectableFrame(
            title="Parsed Transaction",
            body=self.get_content,
        )

    def key_bindings(self) -> KeyBindings:
        kb = KeyBindings()

        @kb.add('up', filter=Condition(lambda: self.activated))
        def _(event):
            self.field_selection.move_selection(-1)

        @kb.add('down', filter=Condition(lambda: self.activated))
        def _(event):
            self.field_selection.move_selection(1)

        @kb.add('s-up', filter=Condition(lambda: self.activated))
        def _(event):
            self.field_selection.move_selection(-self.field_selection.max_view_size)

        @kb.add('s-down', filter=Condition(lambda: self.activated))
        def _(event):
            self.field_selection.move_selection(self.field_selection.max_view_size)

        @kb.add('home', filter=Condition(lambda: self.activated))
        def _(event):
            self.field_selection.move_selection(-self.field_selection.selection)

        @kb.add('end', filter=Condition(lambda: self.activated))
        def _(event):
            self.field_selection.move_selection(len(self.field_selection) - self.field_selection.selection)

        return kb

    @property
    def activated(self) -> bool:
        return self.container.activated

    @activated.setter
    def activated(self, value: bool):
        self.container.activated = value

    def copy_to_clipboard(self):
        if self.transactions.selection_valid():

            t = self.transactions.selected()
            lines = [f"{t.interface}::{t.method} ({t.type()})"]
            for field in self.field_selection.data:
                lines.append(listing._to_indented(field))

            pyperclip.copy("\n".join(lines))

    @property
    def max_height(self) -> int:
        return self._max_height

    @max_height.setter
    def max_height(self, value: int):
        self._max_height = value
        self.field_selection.resize_view(value - 1)

    def update_content(self, _):
        transaction = self.transactions.selected() if self.transactions.selection_valid() else None
        fields = listing.flatten_fields(transaction.fields) if transaction and transaction.fields else []

        self.field_selection.assign(fields)

        self.container.body = self.get_content()

    def get_content(self) -> AnyContainer:

        children = []
        if self.transactions.selection_valid():
            t = self.transactions.selected()
            children.append(
                Window(
                    FormattedTextControl(
                        text=f"{t.interface}::{t.method} ({t.type()})",
                    ),
                    style=f"{t.style()} reverse",
                    height=1
                )
            )
        else:
            children.append(Window(FormattedTextControl(text=""), height=1))

        for i in range(self.field_selection.view.start, self.field_selection.view.end):
            style = "class:field.selected" if self.activated and i == self.field_selection.selection else "class:field.default"
            children.append(Label(
                text=listing._to_indented(self.field_selection[i]),
                style=style))

        padding = self.max_height - len(children)
        children.append(Window(height=padding, char=' '))

        return HSplit(children=children)

    def __pt_container__(self) -> AnyContainer:
        return self.container