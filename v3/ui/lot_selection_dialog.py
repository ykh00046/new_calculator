from PySide6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QDialogButtonBox, QAbstractItemView
from typing import List, Tuple, Optional

class LotSelectionDialog(QDialog):
    """A dialog to select a LOT number from a list of options."""

    def __init__(self, lots_with_dates: List[Tuple[str, str]], parent=None):
        super().__init__(parent)
        self.setWindowTitle("로트 선택")
        self.selected_item = None
        self.lots_data = lots_with_dates

        layout = QVBoxLayout(self)

        self.list_widget = QListWidget()
        # Display LOT and date, but store the tuple
        for lot, date in self.lots_data:
            self.list_widget.addItem(f"{lot} (출고일: {date})")
            
        self.list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        layout.addWidget(self.list_widget)

        # OK and Cancel buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def accept(self):
        """Sets the selected lot tuple when OK is clicked."""
        selected_indexes = self.list_widget.selectedIndexes()
        
        # If no item is explicitly selected but there are items in the list,
        # automatically select the first one.
        if not selected_indexes and self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)
            selected_indexes = self.list_widget.selectedIndexes() # Re-get selected_indexes

        if selected_indexes:
            # Get the original tuple using the index
            self.selected_item = self.lots_data[selected_indexes[0].row()]
        super().accept()

    @staticmethod
    def get_lot(lots_with_dates: List[Tuple[str, str]], parent=None) -> Optional[Tuple[str, str]]:
        """
        Static method to create, show the dialog, and return the selected (LOT, Date) tuple.
        
        Args:
            lots_with_dates: A list of (LOT, Date) tuples to display.
            parent: The parent widget.

        Returns:
            The selected (LOT, Date) tuple, or None if canceled.
        """
        dialog = LotSelectionDialog(lots_with_dates, parent)
        if dialog.exec() == QDialog.Accepted:
            return dialog.selected_item
        return None
