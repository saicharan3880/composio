"""Tool abstractions."""

import base64
import inspect
import os
import traceback
import typing as t
from abc import abstractmethod
from pathlib import Path

import inflection
from pydantic import BaseModel, Field

from composio.tools.base.exceptions import ExecutionFailed
from composio.tools.env.host.workspace import Browsers, FileManagers, Shells

from .abs import Action, ExecuteActionRequest, ExecuteActionResponse, Tool


class FileModel(BaseModel):
    name: str = Field(
        ...,
        description="File name, contains extension to indetify the file type",
    )
    content: bytes = Field(
        ...,
        description="File content in base64",
    )


class LocalAction(
    Action[ExecuteActionRequest, ExecuteActionResponse],
    abs=True,
):
    """Local action abstraction."""

    _shells: t.Callable[[], Shells]
    _browsers: t.Callable[[], Browsers]
    _filemanagers: t.Callable[[], FileManagers]

    @property
    def shells(self) -> Shells:
        return self._shells()

    @property
    def browsers(self) -> Browsers:
        return self._browsers()

    @property
    def filemanagers(self) -> FileManagers:
        return self._filemanagers()


class LocalToolMeta(type):
    """Tool metaclass."""

    def __init__(
        cls,
        name: str,
        bases: t.Tuple,
        dict_: t.Dict,
        autoload: bool = False,
    ) -> None:
        """Initialize action class."""
        if name == "LocalTool":
            return

        cls = t.cast(t.Type[LocalTool], cls)
        for method in ("actions",):
            if getattr(getattr(cls, method), "__isabstractmethod__", False):
                raise RuntimeError(f"Please implement {name}.{method}")

            if not inspect.ismethod(getattr(cls, method)):
                raise RuntimeError(f"Please implement {name}.{method} as class method")

        cls.file = Path(inspect.getfile(cls))
        cls.description = t.cast(str, cls.__doc__).lstrip().rstrip()

        setattr(cls, "name", getattr(cls, "mame", inflection.underscore(cls.__name__)))
        setattr(cls, "enum", getattr(cls, "enum", cls.name).upper())
        setattr(
            cls,
            "display_name",
            getattr(cls, "display_name", inflection.humanize(cls.__name__)),
        )
        setattr(cls, "_actions", getattr(cls, "_actions", {}))
        for action in cls.actions():
            action.tool = cls.name
            action.enum = f"{cls.enum}_{action.name.upper()}"
            cls._actions[action.enum] = action

        if autoload:
            cls.register()


class LocalToolMixin(Tool):
    @classmethod
    @abstractmethod
    def actions(cls) -> t.List[t.Type[LocalAction]]:
        """Get collection of actions for the tool."""

    @classmethod
    def _check_file_uploadable(cls, param: str, model: BaseModel) -> bool:
        return (
            model.model_json_schema()
            .get("properties", {})
            .get(param, {})
            .get("allOf", [{}])[0]
            .get("properties", {})
            or model.model_json_schema()
            .get("properties", {})
            .get(param, {})
            .get("properties", {})
        ) == FileModel.model_json_schema().get("properties")

    @classmethod
    def _process_request(cls, request: t.Dict, model: BaseModel) -> t.Dict:
        """Pre-process request for execution."""
        modified_request_data: t.Dict[str, t.Union[str, t.Dict[str, str]]] = {}
        for param, value in request.items():
            annotations = t.cast(t.Dict, model.model_fields[param].json_schema_extra)
            file_readable = (annotations or {}).get("file_readable", False)
            if file_readable and isinstance(value, str) and os.path.isfile(value):
                _content = Path(value).read_bytes()
                try:
                    _decoded = _content.decode("utf-8")
                except UnicodeDecodeError:
                    _decoded = base64.b64encode(_content).decode("utf-8")
                modified_request_data[param] = _decoded
                continue

            if (
                cls._check_file_uploadable(param=param, model=model)
                and isinstance(value, str)
                and os.path.isfile(value)
            ):
                _content = Path(value).read_bytes()
                modified_request_data[param] = {
                    "name": os.path.basename(value),
                    "content": base64.b64encode(_content).decode("utf-8"),
                }
                continue
            modified_request_data[param] = value
        return modified_request_data

    def execute(
        self,
        action: str,
        params: t.Dict,
        metadata: t.Optional[t.Dict] = None,
    ) -> t.Dict:
        """
        Execute the given action

        :param name: Name of the action.
        :param params: Execution parameters.
        :param metadata: A dictionary containing metadata for action.
        """
        actcls = self._actions.get(action)
        if actcls is None:
            raise ValueError(f"No action found with name `{action}`")

        try:
            metadata = metadata or {}
            instance = actcls(**metadata.get("kwargs", {}))
            if isinstance(instance, LocalAction):
                instance._shells = metadata["_shells"]
                instance._browsers = metadata["_browsers"]
                instance._filemanagers = metadata["_filemanagers"]

            response = instance.execute(
                request=actcls.request.parse(  # type: ignore
                    request=self._process_request(
                        request=params,
                        model=actcls.request.model,  # type: ignore
                    )
                ),
                metadata=metadata,
            )
            return {
                **response.model_dump(),
                "successfull": True,
                "error": None,
            }
        except ExecutionFailed as e:
            self.logger.error(f"Error executing `{action}`: {e}")
            return {
                "successfull": False,
                "error": e.message,
                **e.extra,
            }
        except Exception as e:
            self.logger.error(f"Error executing `{action}`: {e}")
            self.logger.debug(traceback.format_exc())
            return {
                "successfull": False,
                "error": str(e),
            }


class LocalTool(LocalToolMixin, metaclass=LocalToolMeta):
    """Local tool class."""

    gid = "local"
    """Group ID for this tool."""