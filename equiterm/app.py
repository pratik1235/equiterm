"""
Main Equiterm application.
"""

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.binding import Binding

from .screens.main_menu import MainMenuScreen


class EquitermApp(App):
    """Main Equiterm application."""
    
    CSS = '''
    /* Global Styles - Minimalistic */
    Screen {
        background: $surface;
    }
    
    Header {
        background: $surface;
        color: $text;
        text-style: bold;
        border-bottom: solid $primary;
    }
    
    Footer {
        background: $surface;
        color: $text-muted;
        border-top: solid $primary;
    }
    
    /* Main Menu Styles */
    #main-container {
        height: 100%;
        width: 100%;
        align: center middle;
    }
    
    #menu-container {
        width: 60%;
        height: 70%;
        align: center middle;
        background: $surface;
        border: solid $primary;
        padding: 2;
    }
    
    #app-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin: 1;
    }
    
    #subtitle {
        text-align: center;
        color: $text-muted;
        margin-bottom: 2;
    }
    
    #menu-buttons {
        align: center middle;
        width: 100%;
    }
    
    #menu-buttons Button {
        width: 100%;
        margin: 1;
        height: 3;
    }
    
    #help-text {
        text-align: center;
        color: $text-muted;
        margin-top: 2;
    }
    
    /* Fetch Symbol Screen Styles */
    #fetch-container {
        height: 100%;
        width: 100%;
        padding: 1;
    }
    
    #input-section {
        height: auto;
        border: solid $primary;
        margin-bottom: 1;
        padding: 1;
    }
    
    #input-label {
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }
    
    #detected-type {
        color: $success;
        text-style: italic;
        margin-top: 1;
    }
    
    #button-row {
        height: 3;
        margin-top: 1;
        width: 100%;
    }
    
    #button-row Button {
        margin-right: 1;
        width: auto;
        min-width: 15;
    }
    
    #data-section {
        height: 1fr;
        border: solid $primary;
        padding: 1;
    }
    
    #status-text {
        color: $text-muted;
        margin-bottom: 1;
    }
    
    #data-table {
        height: 100%;
        border: solid $primary;
        background: $surface;
    }
    
    /* Create Watchlist Screen Styles */
    #create-container {
        height: 100%;
        width: 100%;
        padding: 1;
    }
    
    #form-section {
        height: 100%;
        border: solid $primary;
        padding: 1;
    }
    
    #form-title {
        text-style: bold;
        color: $primary;
        text-align: center;
        margin-bottom: 2;
    }
    
    #name-label, #symbol-section-title, #symbols-title {
        text-style: bold;
        color: $primary;
        margin: 1 0;
    }
    
    #symbol-inputs {
        height: 3;
        margin: 1 0;
    }
    
    #symbol-inputs Input {
        margin-right: 1;
    }
    
    #symbol-buttons {
        height: 3;
        margin: 1 0;
    }
    
    #symbol-buttons Button {
        margin-right: 1;
    }
    
    #symbols-table {
        height: 1fr;
        margin: 1 0;
    }
    
    #action-buttons {
        height: 3;
        margin-top: 1;
    }
    
    #action-buttons Button {
        margin-right: 1;
    }
    
    /* Watchlist View Screen Styles */
    #watchlist-container {
        height: 100%;
        width: 100%;
        padding: 1;
    }
    
    #watchlist-section {
        height: auto;
        border: solid $primary;
        margin-bottom: 1;
        padding: 1;
    }
    
    #select-label {
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }
    
    #action-buttons {
        height: 3;
        margin: 1 0;
    }
    
    #action-buttons Button {
        margin-right: 1;
    }
    
    #data-section {
        height: 1fr;
        border: solid $primary;
        padding: 1;
    }
    
    #data-title {
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }
    
    #data-table {
        height: 100%;
    }
    
    /* Minimalistic color coding for financial data */
    .green {
        color: $text;
        text-style: bold;
    }
    
    .red {
        color: $text;
        text-style: bold;
    }
    
    .white {
        color: $text;
    }
    
    /* Loading indicator */
    LoadingIndicator {
        color: $primary;
    }
    
    #loading {
        display: none;
    }
    
    /* Error Message Modal */
    #error-message-container {
        width: 60;
        height: 20;
        background: $surface;
        border: solid $error;
        padding: 2;
        align: center middle;
        margin: 4 0;
    }
    
    #error-content {
        align: center middle;
        width: 100%;
        height: 100%;
    }
    
    #error-icon {
        text-align: center;
        text-style: bold;
        color: $error;
        margin-bottom: 1;
        content-align: center middle;
    }
    
    #error-text {
        text-align: center;
        text-style: bold;
        color: $error;
        margin-bottom: 1;
    }
    
    #error-symbol {
        text-align: center;
        color: $text-muted;
        margin-bottom: 1;
    }
    
    #error-hint {
        text-align: center;
        color: $text-muted;
    }
    
    /* Minimalistic button variants */
    Button.-primary {
        background: $surface;
        color: $text;
        border: solid $primary;
    }
    
    Button.-default {
        background: $surface;
        color: $text;
        border: solid $primary;
    }
    
    Button.-error {
        background: $surface;
        color: $text;
        border: solid $error;
    }
    
    /* Input styling */
    Input {
        border: solid $primary;
        background: $surface;
        color: $text;
    }
    
    Input:focus {
        border: solid $accent;
    }
    
    /* DataTable styling */
    DataTable {
        border: solid $primary;
    }
    
    DataTable > .datatable--header {
        background: $primary;
        color: $text;
        text-style: bold;
    }
    
    DataTable > .datatable--cursor {
        background: $accent;
        color: $text;
    }
    
    /* Select widget styling */
    Select {
        border: solid $primary;
        background: $surface;
        color: $text;
    }
    
    Select:focus {
        border: solid $accent;
    }
    '''
    
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("escape", "pop_screen", "Back"),
    ]
    
    def __init__(self):
        super().__init__()
        self.title = "EquiTerm"
        self.sub_title = ""
    
    def compose(self) -> ComposeResult:
        """Compose the main application."""
        yield Container()
    
    def on_mount(self) -> None:
        """Initialize the application."""
        self.push_screen(MainMenuScreen())
    
    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()
    
    def action_pop_screen(self) -> None:
        """Pop the current screen."""
        if len(self.screen_stack) > 1:
            self.pop_screen()


def main():
    """Main entry point for the application."""
    app = EquitermApp()
    app.run()


if __name__ == "__main__":
    main()
