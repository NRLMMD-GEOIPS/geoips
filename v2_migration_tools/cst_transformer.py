import os
from pathlib import Path
import re

import libcst as cst


class ModuleToClassTransformer(cst.CSTTransformer):
    def __init__(self, class_name, base_class, interface_name):
        self.class_name = class_name
        self.base_class = base_class
        self.interface_name = interface_name

        # Convert snake_case → TitleCase
        self.interface_class_name = "".join(
            part.capitalize() for part in interface_name.split("_")
        )

        self.imports = []
        self.class_body = []
        self.module_body = []

    def leave_Module(self, original_node, updated_node):
        body = list(updated_node.body)

        new_body = []

        # --- Step 1: Extract module docstring ---
        docstring = None
        idx = 0

        if (
            body
            and isinstance(body[0], cst.SimpleStatementLine)
            and isinstance(body[0].body[0], cst.Expr)
            and isinstance(body[0].body[0].value, cst.SimpleString)
        ):
            docstring = body[0]
            idx = 1
            new_body.append(docstring)

        # --- Step 2: Collect imports ---
        imports = []
        while idx < len(body) and isinstance(body[idx], (cst.Import, cst.ImportFrom)):
            imports.append(body[idx])
            idx += 1

        # --- Step 3: Create base import ---
        base_import = cst.ImportFrom(
            module=cst.Attribute(
                value=cst.Attribute(
                    value=cst.Attribute(
                        value=cst.Name("geoips"),
                        attr=cst.Name("interfaces"),
                    ),
                    attr=cst.Name("class_based"),
                ),
                attr=cst.Name(self.interface_name),
            ),
            names=[cst.ImportAlias(name=cst.Name(self.base_class))],
        )

        # --- Step 4: Rebuild import section ---
        new_body.extend(imports)

        # Insert your import AFTER existing imports
        new_body.append(base_import)

        # Add a blank line after imports (important for formatting)
        new_body.append(cst.EmptyLine())

        # --- Step 5: Process remaining nodes ---
        for stmt in body[idx:]:
            if isinstance(stmt, cst.SimpleStatementLine):
                if self._is_class_attr(stmt):
                    self.class_body.append(stmt)
                else:
                    new_body.append(stmt)

            elif isinstance(stmt, cst.FunctionDef):
                self.class_body.append(self._convert_function(stmt))

            else:
                new_body.append(stmt)

        # --- Step 6: Build class ---
        # class_def = cst.ClassDef(
        #     name=cst.Name(self.class_name),
        #     bases=[cst.Arg(value=cst.Name(self.base_class))],
        #     body=cst.IndentedBlock(body=self.class_body),
        # )
        # Build class docstring
        docstring_text = self._build_class_docstring()

        docstring_stmt = cst.SimpleStatementLine(
            body=[cst.Expr(value=cst.SimpleString(f'"""{docstring_text}"""'))]
        )

        class_def = cst.ClassDef(
            name=cst.Name(self.class_name),
            bases=[cst.Arg(value=cst.Name(self.base_class))],
            body=cst.IndentedBlock(body=[docstring_stmt, *self.class_body]),
        )

        # Ensure spacing before class
        new_body.append(cst.EmptyLine())
        new_body.append(class_def)
        new_assignment = cst.SimpleStatementLine(
            body=[
                cst.Assign(
                    targets=[cst.AssignTarget(target=cst.Name("PLUGIN_CLASS"))],
                    value=cst.Name(self.class_name),
                )
            ]
        )

        return updated_node.with_changes(body=[*new_body, new_assignment])

    def _is_class_attr(self, stmt):
        TARGETS = {"interface", "name", "family"}

        if not stmt.body:
            return False

        small = stmt.body[0]
        if isinstance(small, cst.Assign):
            target = small.targets[0].target
            if isinstance(target, cst.Name):
                return target.value in TARGETS

        return False

    # def _convert_function(self, func):
    #     if func.name.value == "call":
    #         return func.with_changes(
    #             decorators=[cst.Decorator(decorator=cst.Name("staticmethod"))]
    #         )

    #     # add self if needed
    #     params = func.params
    #     if not params.params or params.params[0].name.value != "self":
    #         new_params = params.with_changes(
    #             params=[cst.Param(name=cst.Name("self"))] + list(params.params)
    #         )
    #         return func.with_changes(params=new_params)

    #     return func

    def _build_class_docstring(self):
        """
        Generate a simple class docstring from the class name.

        Example:
            RgbDefaultAlgorithmPlugin
            -> "RGB Default algorithm plugin class."
        """

        # Remove trailing "Plugin"
        name = self.class_name.removesuffix("Plugin")

        # Split CamelCase
        words = re.findall(r"[A-Z][a-z0-9]*", name)

        if not words:
            return "Plugin class."

        # Last word is usually the plugin type
        plugin_type = words[-1].lower()

        # Convert RGB-style acronyms
        display_words = []
        for word in words[:-1]:
            if len(word) <= 3:
                display_words.append(word.upper())
            else:
                display_words.append(word)

        title = " ".join(display_words)

        return f"{title} {plugin_type} plugin class."

    def _convert_function(self, func):
        params = func.params

        # add self if needed
        if not params.params or params.params[0].name.value != "self":
            new_params = params.with_changes(
                params=[cst.Param(name=cst.Name("self"))] + list(params.params)
            )
            return func.with_changes(params=new_params)

        return func


def write_transformed_module(
    input_path, output_path, class_name, base_class=None, interface_name=None
):
    source = Path(input_path).read_text()

    module = cst.parse_module(source)
    modified = module.visit(
        ModuleToClassTransformer(class_name, base_class, interface_name)
    )
    new_code = modified.code

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    if not os.path.exists(output_path):
        with open(output_path, "w") as f:
            pass
    Path(output_path).write_text(new_code)


def convert_single_file(
    input_file, output_file, class_name, base_class, interface_name
):
    write_transformed_module(
        input_file,
        output_file,
        class_name=class_name,
        base_class=base_class,
        interface_name=interface_name,
    )
