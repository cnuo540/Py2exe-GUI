# Licensed under the GPLv3 License: https://www.gnu.org/licenses/gpl-3.0.html
# For details: https://github.com/muziing/Py2exe-GUI/blob/main/README.md#license

"""此模块主要包含 Python 解释器环境类 `PyEnv`

用于存储 Python 环境的相关信息，如解释器可执行文件路径、Python 版本、已安装的包等
"""

import json
import subprocess
from pathlib import Path
from typing import Optional, Union

from ..Constants import PyEnvType
from ..Utilities import get_sys_python


class PyEnv:
    """Python 解释器环境类，存储某个 Python 解释器对应的环境中的各种信息，如
    解释器可执行文件路径、Python 版本、已安装的包等

    静态方法：
    `PyEnv.get_py_version()` 用于获取 Python 版本号，返回 "3.11.7" 形式的字符串；
    `PyEnv.get_installed_packages()` 用于获取已安装的包，返回一个包含包名和版本的列表；
    `PyEnv.infer_type()` 用于推断 Python 解释器类型，返回 PyEnvType 枚举类的成员；
    """

    def __init__(
        self,
        executable_path: Union[str, Path],
        type_: Optional[PyEnvType] = PyEnvType.unknown,
    ):
        """
        :param executable_path: Python 可执行文件路径
        :param type_: Python 解释器类型，PyEnvType 枚举类的成员。传入显式的 None 则会触发自动识别。
        """

        self.exe_path = str(Path(executable_path).absolute())
        self.pyversion = self.get_py_version(self.exe_path)
        self.installed_packages = self.get_installed_packages(self.exe_path)

        if type_ is None:
            # type_ 为 None 表示特殊含义“待推断”
            self.type = self.infer_type(self.exe_path)
        else:
            self.type = type_

    def __repr__(self) -> str:
        return f"PyEnv object (executable_path={self.exe_path}, type={self.type})"

    @staticmethod
    def get_py_version(executable_path: Union[str, Path]) -> str:
        """获取Python解释器的版本，以形如 "3.11.7" 的字符串形式返回

        :param executable_path: Python 可执行文件路径
        :return: Version of the Python interpreter, such as "3.11.7".
        """

        cmd = [
            f"{executable_path}",
            "-c",
            "import platform;print(platform.python_version(), end='')",
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            version = result.stdout
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to get Python version: {e.output}") from e
        return version

    @staticmethod
    def get_installed_packages(executable_path: Union[str, Path]) -> list[dict]:
        """获取该 Python 环境中已安装的包信息

        :param executable_path: Python 解释器可执行文件路径
        :return: 包列表，形如 [{'name': 'aiohttp', 'version': '3.9.1'}, {'name': 'aiosignal', 'version': '1.3.1'}, ...]
        """

        cmd = [
            f"{executable_path}",
            "-m",
            "pip",
            "list",
            "--format",
            "json",
            "--disable-pip-version-check",
            "--no-color",
            "--no-python-version-warning",
        ]

        try:
            # 运行 pip list 命令，获取输出
            result = subprocess.run(cmd, capture_output=True, text=True)
            pip_list = result.stdout
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to get installed packages: {e.output}") from e
        except Exception as e:
            raise RuntimeError(f"An error occurred: {e}") from e

        try:
            # json 解析
            installed_packages: list[dict] = json.loads(pip_list)
        except json.decoder.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse installed packages: {e}") from e

        return installed_packages

    @staticmethod
    def infer_type(executable_path: Union[str, Path]) -> PyEnvType:
        """推断 Python 环境类型，如 system venv Poetry Conda 等

        暂时仅通过解析解释器绝对路径，字符串正则匹配来判断，有待改进

        :param executable_path: Python 可执行文件路径
        :return: PyEnvType 枚举类的成员
        """

        # 确保路径为 POSIX 风格的绝对路径
        exe_path = Path(executable_path).absolute().as_posix()

        # # 使用正则表达式匹配来检测不同的环境类型
        # regexes = [
        #     (r"^.*venv.*", PyEnvType.venv),
        #     (r"^.*pypoetry.*", PyEnvType.poetry),
        #     (r"^.*conda.*", PyEnvType.conda),
        #     (
        #         re.escape(f"{Path(get_sys_python()).absolute().as_posix()}"),
        #         PyEnvType.system
        #     )]
        # for regex, env_type in regexes:
        #     match = re.search(regex, str(exe_path))
        #     if match:
        #         return env_type

        # 简单的字符串 in 方法，效率应该远高于正则匹配
        match_pair = [
            ("venv", PyEnvType.venv),
            ("pypoetry", PyEnvType.poetry),
            ("conda", PyEnvType.conda),
            (f"{Path(get_sys_python()).absolute().as_posix()}", PyEnvType.system),
        ]

        for patten, env_type in match_pair:
            if patten in exe_path:
                return env_type

        # 如果没有匹配到，返回 unknown
        return PyEnvType.unknown

    def pkg_installed(self, package_name: str) -> bool:
        """检查特定软件包是否已安装

        :param package_name: 待检索的软件包名称
        :return: 是否已安装
        """

        return any(pkg["name"] == package_name for pkg in self.installed_packages)
