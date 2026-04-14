"""InfoBar 토스트 알림 헬퍼."""

from qfluentwidgets import InfoBar, InfoBarPosition


def show_success(parent, title: str, content: str, duration: int = 2000) -> None:
    InfoBar.success(
        title=title,
        content=content,
        parent=parent,
        position=InfoBarPosition.TOP_RIGHT,
        duration=duration,
    )


def show_warning(parent, title: str, content: str, duration: int = 3000) -> None:
    InfoBar.warning(
        title=title,
        content=content,
        parent=parent,
        position=InfoBarPosition.TOP_RIGHT,
        duration=duration,
    )


def show_error(parent, title: str, content: str, duration: int = 4000) -> None:
    InfoBar.error(
        title=title,
        content=content,
        parent=parent,
        position=InfoBarPosition.TOP_RIGHT,
        duration=duration,
    )


def show_info(parent, title: str, content: str, duration: int = 2500) -> None:
    InfoBar.info(
        title=title,
        content=content,
        parent=parent,
        position=InfoBarPosition.TOP_RIGHT,
        duration=duration,
    )
