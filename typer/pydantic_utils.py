from typing import Any, List, Tuple, Type

import click
import pydantic
from typer.models import ParamMeta

PYDANTIC_FIELD_SEPARATOR = "_"


class ModelBuilder:
    def __init__(self, field_convertors, model_type):
        self.field_convertors = field_convertors
        self.model_type = model_type
        self.data = {}

    def __call__(self, field_full_name: str, field_value: Any):
        model_name, field_name = field_full_name.rsplit(
            PYDANTIC_FIELD_SEPARATOR, maxsplit=1
        )
        self.data[field_name] = field_value

        model = None
        try:
            model = self.model_type(**self.data)
        except pydantic.ValidationError:
            pass

        return model_name, model


def get_click_params(param: ParamMeta) -> Tuple[List[click.Option], Any]:
    from typer import Option
    from typer.main import get_click_param, lenient_issubclass

    model_type: Type[pydantic.BaseModel] = param.annotation
    params = []
    field_convertors = {}
    for field_name, field in model_type.__fields__.items():
        if lenient_issubclass(field.type_, pydantic.BaseModel):
            raise ValueError("Nested models not supported yet.")

        param_name = f"{param.name}{PYDANTIC_FIELD_SEPARATOR}{field.name}"
        field_param, field_convertor = get_click_param(
            ParamMeta(
                name=param_name,
                annotation=field.type_,
                default=Option(default=field.default),
            )
        )
        params.append(field_param)
        field_convertors[param_name] = field_convertor

    model_builder = ModelBuilder(field_convertors, model_type)
    return params, model_builder
