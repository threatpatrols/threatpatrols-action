import argparse
import sys
from typing import Any

from pydantic_core import PydanticUndefined

from ...config import config
from ...shared.lib.casts import annotation_to_type_name
from ...shared.lib.color import ansicode
from .. import tpas_commands, tpas_non_action_commands


def parse_action_args(fields: dict[str, Any] = None) -> dict:
    parser = argparse.ArgumentParser(
        prog=config.TITLE,
        description=f"{config.TITLE}: v{config.VERSION} | TPAS:v{config.TPAS_VERSION}\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,
        epilog="Docs: https://docs.threatpatrols.com/tpas",
    )

    # tpas args
    parse_tpas_args(parser)

    # dynamic args based on fields
    parse_fields_args(parser, fields)

    # --debug
    parser.add_argument(
        "--debug",
        "-d",
        action="store_true",
        default=False,
        help="Enable debug level logging.",
    )

    # --quiet
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        default=False,
        help="Enable error-only level logging; overrides --debug option.",
    )

    if len(sys.argv) < 2 or "--help" in sys.argv:
        parser.print_help()
        if "--help" in sys.argv:
            sys.exit(0)
        sys.exit(1)

    parsed = parser.parse_args()

    if parsed.quiet:
        parsed.debug = False

    return vars(parsed)


def parse_fields_args(parser: argparse.ArgumentParser, fields: dict[str, Any]):

    action_args = parser.add_argument_group(f"{config.ACTION_NAME} args")
    is_require_override = any(map(lambda v: v in tpas_non_action_commands, sys.argv))  # sneaky punishment
    action_args.add_argument(
        "--tpas-require-override", required=False, help=argparse.SUPPRESS, default=is_require_override
    )

    for field, field_info in fields.items():

        arg_full = f"--{field.replace('_', '-').strip()}"
        parser_argument_args = [arg_full]

        parser_argument_kwargs = {
            "default": None if field_info.get_default() is PydanticUndefined else field_info.get_default(),
            "required": True if (field_info.is_required() and is_require_override is False) else False,
        }

        arg_type_name = annotation_to_type_name(annotation=field_info.annotation)

        if arg_type_name not in ("str", "bool", "list", "dict", "int", "float"):
            raise TypeError(f"Field {field!r} with type-{arg_type_name!r} is not a supported type.")

        arg_help = f"{field.replace('_', ' ').title()} {arg_type_name}-type value"

        if arg_type_name == "bool":
            parser_argument_kwargs["action"] = "store_true"
        else:
            parser_argument_kwargs["metavar"] = f"<{arg_type_name}>"

        if arg_type_name == "list":
            parser_argument_kwargs["nargs"] = "+"
        elif arg_type_name == "dict":
            parser_argument_kwargs["nargs"] = "+"
            arg_help += ", provide in '<key>:<value>' format"
        arg_help += "."

        if field_info.is_required():
            arg_help += f" {ansicode.WARNING}[required; tpas-command=call]{ansicode.ENDC}"

        parser_argument_kwargs["help"] = arg_help

        action_args.add_argument(*parser_argument_args, **parser_argument_kwargs)


def parse_tpas_args(parser: argparse.ArgumentParser):

    tpas_args = parser.add_argument_group("tpas-action")

    tpas_args.add_argument(
        "--tpas-command",
        required=True,
        metavar="<str>",
        nargs="+",
        help="Action command {} {} {} {}[required]{} \nUse call_id/task_id as second arg in *-get commands.".format(
            "{", ",".join(tpas_commands), "}", ansicode.WARNING, ansicode.ENDC
        ),
    )

    tpas_args.add_argument(
        "--tpas-tags",
        required=False,
        metavar="<dict>",
        nargs="+",
        help="Additional tags for this action, provide in '<key>:<value>' format.",
    )

    tpas_args.add_argument(
        "--tpas-action",
        required=False,
        metavar="<str>",
        help=argparse.SUPPRESS,
        # help=f"Override the TPAS action-name. [default: {config.ACTION_NAME}]",
    )
