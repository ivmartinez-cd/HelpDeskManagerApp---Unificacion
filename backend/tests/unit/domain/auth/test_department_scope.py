import uuid

from src.modules.auth.domain.value_objects.department_scope import (
    GlobalScope,
    SingleDepartment,
)


def test_global_scope_and_single_department_are_distinguishable() -> None:
    dept_id = uuid.uuid4()

    scopes: list[GlobalScope | SingleDepartment] = [GlobalScope(), SingleDepartment(dept_id)]

    assert isinstance(scopes[0], GlobalScope)
    assert isinstance(scopes[1], SingleDepartment)
    assert scopes[1].department_id == dept_id
