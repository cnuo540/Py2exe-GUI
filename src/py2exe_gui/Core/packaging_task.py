# Licensed under the GPLv3 License: https://www.gnu.org/licenses/gpl-3.0.html
# For details: https://github.com/muziing/Py2exe-GUI/blob/main/README.md#license

"""此模块主要包含打包任务类 `PackagingTask`，用于进行选项值检查和保存最终使用的选项

`PackagingTask.using_option` 是一个数据类型为 dict[PyInstOpt, Any] 的字典，存储着当前确认使用的所有选项
"""

__all__ = ["PackagingTask"]

from pathlib import Path
from typing import Any, Optional

from PySide6 import QtCore

from ..Constants import PyInstOpt
from ..Utilities import PyEnv
from .validators import FilePathValidator


class PackagingTask(QtCore.QObject):
    """打包任务类，处理用户输入

    接收来自界面的用户输入操作并处理，将结果反馈给界面和实际执行打包子进程的 `Packaging` 对象
    在实例属性 `pyenv` 中保存目前设置的 Python 环境；
    在实例属性 `using_option` 中保存目前设置的所有参数值；
    """

    # 自定义信号
    option_set = QtCore.Signal(tuple)  # 用户输入选项通过了验证，已设置为打包选项；
    # option_set 实际类型为 tuple[PyInstOpt, Any]
    option_error = QtCore.Signal(PyInstOpt)  # 用户输入选项有误，需要进一步处理
    ready_to_pack = QtCore.Signal(bool)  # 是否已经可以运行该打包任务

    def __init__(self, parent: Optional[QtCore.QObject] = None) -> None:
        """
        :param parent: 父控件对象
        """

        super().__init__(parent)

        # 保存打包时使用的 Python 环境
        self.pyenv: Optional[PyEnv] = None

        # 保存所有参数值，None表示未设置
        self.using_option: dict[PyInstOpt, Any] = {value: None for value in PyInstOpt}
        # TODO: 设法为值补充类型注解

        # self.script_path: Optional[Path] = None
        # self.icon_path: Optional[Path] = None
        # self.add_data_list: Optional[list[AddDataWindow.data_item]] = None
        # self.add_binary_list: Optional[list[AddDataWindow.data_item]] = None
        # self.out_name: Optional[str] = None
        # self.FD: Optional[bool] = None
        # self.console: Optional[str] = None
        # self.hidden_import: Optional[list[str]] = None
        # self.clean: Optional[bool] = None

    @QtCore.Slot(tuple)
    def on_opt_selected(self, option: tuple[PyInstOpt, Any]) -> None:
        """槽函数，处理用户在界面选择的打包选项，进行有效性验证并保存

        :param option: 选项，应为二元素元组，且其中的第一项为 `PyInstOpt` 枚举值
        :raise TypeError: 如果传入的 option 参数第一项不是有效的 PyInstOpt 成员，则抛出类型错误
        """

        arg_key, arg_value = option

        # 进行有效性验证，有效则保存并发射option_set信号，无效则发射option_error信号
        if arg_key == PyInstOpt.script_path:
            script_path = Path(arg_value)
            if FilePathValidator.validate_script(script_path):
                self.using_option[PyInstOpt.script_path] = script_path
                self.ready_to_pack.emit(True)
                self.option_set.emit(option)
                self.using_option[PyInstOpt.out_name] = script_path.stem  # 输出名默认与脚本名相同
                self.option_set.emit((PyInstOpt.out_name, script_path.stem))
            else:
                self.ready_to_pack.emit(False)
                self.option_error.emit(arg_key)

        elif arg_key == PyInstOpt.icon_path:
            icon_path = Path(arg_value)
            if FilePathValidator.validate_icon(icon_path):
                self.using_option[PyInstOpt.icon_path] = icon_path
                self.option_set.emit(option)
            else:
                self.option_error.emit(arg_key)

        elif isinstance(arg_key, PyInstOpt):
            # 其他不需要进行检查的选项，直接保存与发射完成设置信号
            self.using_option[arg_key] = arg_value
            self.option_set.emit(option)

        else:
            raise TypeError(f"'{arg_key}' is not a instance of {PyInstOpt}.")
