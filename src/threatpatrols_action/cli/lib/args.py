import argparse
import sys
from typing import Any

from pydantic_core import PydanticUndefined

from ...config import config
from ...shared.lib.casts import annotation_to_type_name
from ...shared.lib.color import ansicode
from .. import tpas_action_commands, tpas_commands

EPILOG = f"""
Some TPAS (Threat Patrols Actions) commands require additional positional arguments:
  - call: invokes the {config.ACTION_NAME} action directly using the named tpas-call action args, no additional args.
  - call-get/task-get: returns call/task data; must append a call_id/task_id as an additional arg.
  - call-list/task-list: returns a list of non-expired item-summaries, use 'expired' or 'expired-purge' args. 

TPAS callbacks must be defined in your config.yml before they can be referenced in --tpas-callbacks.

Docs: https://docs.threatpatrols.com/tpas
"""


def parse_action_args(fields: dict[str, Any] = None) -> dict:
    parser = argparse.ArgumentParser(
        prog=f"tpas-{config.ACTION_NAME}",
        description=f"{config.TITLE}: v{config.VERSION} | Threat Patrols Actions: v{config.TPAS_VERSION}\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,
        epilog=EPILOG,
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

    action_args = parser.add_argument_group(f"tpas-call {config.ACTION_NAME} args")
    is_require_override = not any(map(lambda v: v in tpas_action_commands, sys.argv))  # punishment
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
            raise ValueError(f"Field {field!r} with type-{arg_type_name!r} is not a supported type.")

        arg_help = f"{field.replace('_', ' ').title()} {arg_type_name}-type value"

        if arg_type_name == "bool":
            parser_argument_kwargs["action"] = "store_true"
        else:
            parser_argument_kwargs["metavar"] = f"<{arg_type_name}>"

        if arg_type_name == "list":
            parser_argument_kwargs["nargs"] = "+"
        elif arg_type_name == "dict":
            parser_argument_kwargs["nargs"] = "+"
            arg_help += ", items provided in '<key>:<value>' format"
        arg_help += "."

        if field_info.is_required():
            arg_help += (
                f" {ansicode.WARNING}[required]{ansicode.ENDC} " f"{ansicode.OKBLUE}[tpas-command: call]{ansicode.ENDC}"
            )

        parser_argument_kwargs["help"] = arg_help

        action_args.add_argument(*parser_argument_args, **parser_argument_kwargs)


def parse_tpas_args(parser: argparse.ArgumentParser):

    tpas_command_args = parser.add_argument_group("tpas-command")

    tpas_command_args.add_argument(
        "tpas_command",
        metavar="<cmd> [<args> ...]",
        nargs="+",
        help="TPAS command {} {} {} {}[required]{} {}[see below]{}".format(
            "{", ", ".join(tpas_commands), "}", ansicode.WARNING, ansicode.ENDC, ansicode.OKBLUE, ansicode.ENDC
        ),
    )

    # ===

    tpas_action_args = parser.add_argument_group("tpas-call")

    tpas_action_args.add_argument(
        "--tpas-tags",
        required=False,
        metavar="<dict>",
        nargs="*",
        help="Additional tags for this action, items provided in '<key>:<value>' format.",
    )

    tpas_action_args.add_argument(
        "--tpas-callbacks",
        required=False,
        metavar="<dict>",
        nargs="*",
        help="Callbacks for this action, items provided in '<callback-name>:<config-name>' format.",
    )

    tpas_action_args.add_argument(
        "--tpas-action",
        required=False,
        metavar="<str>",
        help=argparse.SUPPRESS,
        # help=f"Override the TPAS action-name. [default: {config.ACTION_NAME}]",
    )
