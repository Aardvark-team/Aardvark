from Types import (
    Object,
    Number,
    String,
    Array,
    Set,
    Boolean,
    Null,
    Scope,
    _Undefined,
    Function,
)


def render(object, formatting={}):
    if type(object) == Number or type(object) == int or type(object) == float:
        return str(object)
    elif isinstance(object, str):
        obj = str(object).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        return f'"{obj}"'
    elif (
        object == Null
        or object == None
        or type(object) == _Undefined
        or object == _Undefined
    ):
        return "null"
    elif type(object) == Boolean or object == True or object == False:
        return str(object).lower()
    elif type(object) == Set:
        return f"{{{', '.join([render(x) for x in object.value])}}}"
    elif type(object) == Array:
        return f"[{', '.join([render(x) for x in object.value])}]"
    elif type(object) == Object or type(object) == Scope:
        string = "{"
        for key, value in object.vars.items():
            if value == object:
                continue
            value = render(value)
            if value == None:
                continue
            key = render(key)
            string += key + ":" + value + ","
        return string[:-1] + "}"
    elif getattr(object, "to_json", None):
        return render(object.to_json())
    else:
        # print(object, type(object))
        # raise Exception(f"Cannot render object: {object}")
        return None


def test():
    print(
        render(
            Object(
                {"x": Array([1, 2, 3]), "y": Object({"uhr": 948, "njf": Boolean(True)})}
            )
        ),
        render(
            Scope(
                {"x": Array([1, 2, 3]), "y": Scope({"uhr": 948, "njf": Boolean(True)})}
            )
        ),
        render(
            Array(
                [
                    Object(
                        {
                            "x": Array([1, 2, 3]),
                            "y": Object({"uhr": 948, "njf": Boolean(True)}),
                        }
                    ),
                    Object(
                        {
                            "x": Array([1, 2, 3]),
                            "y": Object({"uhr": 948, "njf": Boolean(True)}),
                        }
                    ),
                ],
            )
        ),
    )


if __name__ == "__main__":
    test()
